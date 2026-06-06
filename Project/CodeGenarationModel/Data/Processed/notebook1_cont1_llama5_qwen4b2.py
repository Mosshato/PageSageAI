%%capture
import os
!pip install pip3-autoremove
!pip install torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu128
!pip install unsloth
!pip install transformers==4.56.2
!pip install --no-deps trl==0.22.2
!pip install peft accelerate bitsandbytes datasets -q
!pip install evaluate sacrebleu rouge_score codebleu huggingface_hub pynvml -q







import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from unsloth import FastLanguageModel
import json, time, gc, datetime
import torch
import numpy as np
from datasets import Dataset
from transformers import AutoTokenizer, TrainingArguments, BitsAndBytesConfig
from trl import SFTTrainer
from huggingface_hub import HfApi, login
import evaluate
from codebleu import calc_codebleu
from kaggle_secrets import UserSecretsClient

secrets  = UserSecretsClient()
HF_TOKEN = secrets.get_secret("HF_TOKEN")
HF_USER  = "Mosshato"
login(token=HF_TOKEN)
api = HfApi()

DATASET_DIR = "/kaggle/input/manimdata1bsc"
WORK_DIR    = "/kaggle/working"
METRICS_DIR = os.path.join(WORK_DIR, "metrics")
os.makedirs(METRICS_DIR, exist_ok=True)

if torch.cuda.is_available():
    cc = torch.cuda.get_device_capability(0)
    print(f"✅ GPU   : {torch.cuda.get_device_name(0)}")
    print(f"   VRAM  : {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")
    print(f"   CC    : {cc[0]}.{cc[1]}")
else:
    print("❌ CUDA indisponibil!")

print(f"✅ PyTorch : {torch.__version__}")
print("✅ Setup complet")



BNBCONFIG = BitsAndBytesConfig(
    load_in_4bit              = True,
    bnb_4bit_quant_type       = "nf4",
    bnb_4bit_compute_dtype    = torch.float16,
    bnb_4bit_use_double_quant = True,
)


def load_jsonl(path):
    """Citeste un fisier .jsonl si returneaza o lista de dictionare."""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

train_data = load_jsonl("/kaggle/input/datasets/krisztasoos/manimdata1bsc/train.jsonl")
val_data   = load_jsonl("/kaggle/input/datasets/krisztasoos/manimdata1bsc/val.jsonl")
test_data  = load_jsonl("/kaggle/input/datasets/krisztasoos/manimdata1bsc/test.jsonl")

print(f"✅ Dataset încărcat:")
print(f"   Train : {len(train_data)} exemple")
print(f"   Val   : {len(val_data)} exemple")
print(f"   Test  : {len(test_data)} exemple")

# ── Verificare structură ──────────────────────────────────────
sample = train_data[0]
print(f"\n🔍 Câmpuri disponibile: {list(sample.keys())}")
print(f"   INSTRUCTION : {sample.get('instruction', 'N/A')[:80]}...")
print(f"   INPUT       : {sample.get('input',       'N/A')[:80]}...")
print(f"   OUTPUT      : {sample.get('output',      'N/A')[:80]}...")




ALPACA_TEMPLATE = """\
Below is an instruction that describes a task, paired with an input \
that provides further context. Write a response that appropriately \
completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""

def format_prompt(row, eos_token, add_eos=True):
    """
    Formateaza un row din dataset in format Alpaca.
    add_eos=True pentru train/val, False pentru inference.
    """
    text = ALPACA_TEMPLATE.format(
        instruction = row.get("instruction", ""),
        input       = row.get("input", ""),
        output      = row.get("output", ""),
    )
    if add_eos:
        text += eos_token
    return {"text": text}

def make_hf_dataset(data, tokenizer):
    """Converteste lista de dictionare in HuggingFace Dataset formatat."""
    ds = Dataset.from_list(data)
    ds = ds.map(
        lambda x: format_prompt(x, tokenizer.eos_token, add_eos=True),
        batched=False,
    )
    return ds

print("✅ Prompt template Alpaca definit")
print("\n📋 Preview template:")
print(ALPACA_TEMPLATE.format(
    instruction="Generate a Manim animation",
    input="Draw a circle that moves to the right",
    output="# [cod manim aici]"
))


# ── Incarcare metrici ─────────────────────────────────────────
bleu_metric  = evaluate.load("sacrebleu")
rouge_metric = evaluate.load("rouge")

# ── Metrici custom ────────────────────────────────────────────
def compute_exact_match(preds, refs):
    """Procentul de predictii identice cu referinta (case-insensitive strip)."""
    matches = sum(p.strip() == r.strip() for p, r in zip(preds, refs))
    return matches / len(refs) if refs else 0.0

def compute_token_accuracy(preds, refs, tokenizer):
    """
    Acuratete la nivel de token: cate tokene generate
    coincid pozitional cu tokenii din referinta.
    """
    total, correct = 0, 0
    for p, r in zip(preds, refs):
        pred_tokens = tokenizer.encode(p)
        ref_tokens  = tokenizer.encode(r)
        min_len     = min(len(pred_tokens), len(ref_tokens))
        correct    += sum(a == b for a, b in zip(pred_tokens[:min_len], ref_tokens[:min_len]))
        total      += max(len(pred_tokens), len(ref_tokens))
    return correct / total if total > 0 else 0.0

def generate_predictions(model, tokenizer, data, max_new_tokens=512, batch_size=4):
    """
    Genereaza predictii pentru toate exemplele din data.
    Foloseste batch_size pentru eficienta — ajusteaza in jos daca OOM.
    """
    model.eval()
    preds = []

    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]

        # Cream prompt-ul FARA output (modelul trebuie sa il genereze)
        prompts = [
            ALPACA_TEMPLATE.format(
                instruction = r.get("instruction", ""),
                input       = r.get("input", ""),
                output      = "",        # ← gol intentionat
            )
            for r in batch
        ]

        inputs = tokenizer(
            prompts,
            return_tensors  = "pt",
            padding         = True,
            truncation      = True,
            max_length      = 2048,
        ).to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens = max_new_tokens,
                do_sample      = False,          # greedy decode — reproductibil
                pad_token_id   = tokenizer.eos_token_id,
            )

        # Extragem doar tokenii generati (fara prompt)
        input_len = inputs["input_ids"].shape[1]
        for out in outputs:
            generated = tokenizer.decode(
                out[input_len:], skip_special_tokens=True
            )
            preds.append(generated.strip())

        # Eliberam memoria dupa fiecare batch
        del inputs, outputs
        torch.cuda.empty_cache()

    return preds

def evaluate_model(model, tokenizer, test_data, run_name):
    """
    Evaluare completa: genereaza predictii si calculeaza toate metricile.
    Salveaza rezultatele in METRICS_DIR/run_name_metrics.json.
    """
    print(f"\n📊 Evaluare: {run_name}")

    refs  = [r["output"] for r in test_data]
    preds = generate_predictions(model, tokenizer, test_data)

    # ── BLEU ──────────────────────────────────────
    bleu = bleu_metric.compute(
        predictions = preds,
        references  = [[r] for r in refs],    # sacrebleu vrea lista de liste
    )["score"]

    # ── ROUGE ─────────────────────────────────────
    rouge = rouge_metric.compute(predictions=preds, references=refs)

    # ── Exact Match & Token Accuracy ──────────────
    em  = compute_exact_match(preds, refs)
    tok = compute_token_accuracy(preds, refs, tokenizer)

    # ── CodeBLEU ──────────────────────────────────
    try:
        cb_result      = calc_codebleu(refs, preds, lang="python",
                                       weights=(0.25, 0.25, 0.25, 0.25))
        codebleu_score = cb_result["codebleu"]
    except Exception as e:
        print(f"   ⚠️  CodeBLEU error: {e}")
        codebleu_score = -1.0

    metrics = {
        "run_name"         : run_name,
        "bleu"             : round(bleu, 4),
        "rouge1"           : round(rouge["rouge1"], 4),
        "rouge2"           : round(rouge["rouge2"], 4),
        "rougeL"           : round(rouge["rougeL"], 4),
        "rougeLsum"        : round(rouge["rougeLsum"], 4),
        "exact_match"      : round(em, 4),
        "token_accuracy"   : round(tok, 4),
        "codebleu"         : round(codebleu_score, 4),
        "num_test_samples" : len(test_data),
        "timestamp"        : datetime.datetime.now().isoformat(),
    }

    # ── Print sumar ────────────────────────────────
    print(f"   BLEU          : {metrics['bleu']}")
    print(f"   CodeBLEU      : {metrics['codebleu']}")
    print(f"   ROUGE-L       : {metrics['rougeL']}")
    print(f"   Exact Match   : {metrics['exact_match']}")
    print(f"   Token Accuracy: {metrics['token_accuracy']}")

    # ── Salvare metrici individuale ────────────────
    metrics_path = os.path.join(METRICS_DIR, f"{run_name}_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"   💾 Metrici salvate: {metrics_path}")

    return metrics, preds

print("✅ Funcții evaluare definite")



def save_run(model, tokenizer, config, metrics, preds, run_name):
    """
    Salveaza complet un run:
      - adaptorul LoRA (weights fine-tuned)
      - tokenizer
      - config.json (hyperparametrii)
      - metrics.json
      - predictions.jsonl
    """
    local_path = os.path.join(WORK_DIR, run_name)
    os.makedirs(local_path, exist_ok=True)

    # ── LoRA adapter + tokenizer ──────────────────
    model.save_pretrained(local_path)
    tokenizer.save_pretrained(local_path)

    # ── Config (hyperparametrii) ──────────────────
    config_path = os.path.join(local_path, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # ── Metrici ───────────────────────────────────
    metrics_path = os.path.join(local_path, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Predictii ─────────────────────────────────
    preds_path = os.path.join(local_path, "predictions.jsonl")
    with open(preds_path, "w") as f:
        for pred in preds:
            f.write(json.dumps({"prediction": pred}) + "\n")

    print(f"   💾 Salvat local: {local_path}")
    return local_path

def push_to_hf(local_path, run_name, private=True):
    """
    Uploadeaza folderul local pe HuggingFace Hub ca model repo privat.
    Daca repo-ul nu exista, il creeaza automat.
    """
    repo_id = f"{HF_USER}/{run_name}"
    try:
        api.create_repo(
            repo_id    = repo_id,
            repo_type  = "model",
            exist_ok   = True,       # nu crapa daca exista deja
            private    = private,
        )
        api.upload_folder(
            folder_path = local_path,
            repo_id     = repo_id,
            repo_type   = "model",
            token       = HF_TOKEN,
        )
        print(f"   🚀 Upload HF: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"   ⚠️  HF upload eroare: {e}")

def append_global_metrics(metrics, run_name):
    """
    Adauga metricile unui run la fisierul global all_metrics.jsonl.
    Append mode — nu suprascrie rezultatele anterioare.
    """
    global_path = os.path.join(METRICS_DIR, "all_metrics.jsonl")
    with open(global_path, "a") as f:
        f.write(json.dumps({"run": run_name, **metrics}) + "\n")
    print(f"   📝 Metrici globale actualizate: {global_path}")

print("✅ Funcții salvare definite")





# ── Model țintă ───────────────────────────────────────────────
MODEL_CONFIG = {
    "hf_name"    : "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    "short_name" : "llama3.1-8b",
    "max_seq_len": 2048,
}

# ── 5 Configurații LoRA ───────────────────────────────────────
CONFIGS = [
    {
        "config_id"                  : "cfg1",
        "description"                : "Baseline — r=8, lr=2e-4, 3 epoci",
        "r"                          : 8,
        "lora_alpha"                 : 16,
        "lora_dropout"               : 0.05,
        "learning_rate"              : 2e-4,
        "num_train_epochs"           : 3,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "warmup_steps"               : 50,
        "weight_decay"               : 0.01,
        "lr_scheduler_type"          : "cosine",
        "max_seq_length"             : 512,
    },
    {
        "config_id"                  : "cfg2",
        "description"                : "Rank mare — r=16",
        "r"                          : 16,
        "lora_alpha"                 : 32,
        "lora_dropout"               : 0.05,
        "learning_rate"              : 2e-4,
        "num_train_epochs"           : 3,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "warmup_steps"               : 50,
        "weight_decay"               : 0.01,
        "lr_scheduler_type"          : "cosine",
        "max_seq_length"             : 512,
    },
    {
        "config_id"                  : "cfg3",
        "description"                : "LR mic — lr=5e-5",
        "r"                          : 8,
        "lora_alpha"                 : 16,
        "lora_dropout"               : 0.05,
        "learning_rate"              : 5e-5,
        "num_train_epochs"           : 3,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "warmup_steps"               : 50,
        "weight_decay"               : 0.01,
        "lr_scheduler_type"          : "cosine",
        "max_seq_length"             : 512,
    },
    {
        "config_id"                  : "cfg4",
        "description"                : "Mai multe epoci — 5 epoci",
        "r"                          : 8,
        "lora_alpha"                 : 16,
        "lora_dropout"               : 0.05,
        "learning_rate"              : 2e-4,
        "num_train_epochs"           : 5,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "warmup_steps"               : 100,
        "weight_decay"               : 0.01,
        "lr_scheduler_type"          : "cosine",
        "max_seq_length"             : 512,
    },
    {
        "config_id"                  : "cfg5",
        "description"                : "Scheduler linear + dropout mare",
        "r"                          : 8,
        "lora_alpha"                 : 16,
        "lora_dropout"               : 0.1,
        "learning_rate"              : 1e-4,
        "num_train_epochs"           : 3,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "warmup_steps"               : 50,
        "weight_decay"               : 0.01,
        "lr_scheduler_type"          : "linear",
        "max_seq_length"             : 512,
    },
]

print(f"✅ {len(CONFIGS)} configurații definite pentru {MODEL_CONFIG['short_name']}")
for c in CONFIGS:
    print(f"   {c['config_id']}: {c['description']}")



    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

all_metrics = []
import gc
for run_idx, config in enumerate(CONFIGS):
    
    gc.collect()
    torch.cuda.empty_cache()
    
    config    = config.copy()   # nu modificam originalul
    run_name  = f"{MODEL_CONFIG['short_name']}-{config['config_id']}"
    print(f"\n{'='*60}")
    print(f"RUN {run_idx+1}/{len(CONFIGS)}: {run_name}")
    print(f"  {config['description']}")
    print(f"{'='*60}")

    # ── 1. Curata memoria inainte de incarcare ────────────────
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    # ── 2. Incarcare model + tokenizer cu Unsloth ─────────────
    print("⏳ Încarcare model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name      = MODEL_CONFIG["hf_name"],
        max_seq_length  = config["max_seq_length"],
        dtype           = None,          # auto: fp16 pe T4
        load_in_4bit    = True,
        token           = HF_TOKEN,
        device_map      = {"": 0}, # Add this! Forces the first GPU
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ── 3. Aplica LoRA cu Unsloth ─────────────────────────────
    model = FastLanguageModel.get_peft_model(
        model,
        r                        = config["r"],
        lora_alpha               = config["lora_alpha"],
        lora_dropout             = config["lora_dropout"],
        target_modules           = ["q_proj","k_proj","v_proj","o_proj",
                                    "gate_proj","up_proj","down_proj"],
        bias                     = "none",
        use_gradient_checkpointing= "unsloth",   # custom, ~30% mai putina VRAM
        random_state             = 42,
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"   Parametri antrenabili: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    # ── 4. Pregatire dataset ───────────────────────────────────
    train_ds = make_hf_dataset(train_data, tokenizer)
    val_ds   = make_hf_dataset(val_data,   tokenizer)

    # ── 5. Training arguments ─────────────────────────────────
    training_args = TrainingArguments(
        output_dir                  = os.path.join(WORK_DIR, f"tmp_{run_name}"),
        num_train_epochs            = config["num_train_epochs"],
        per_device_train_batch_size = config["per_device_train_batch_size"],
        gradient_accumulation_steps = config["gradient_accumulation_steps"],
        warmup_steps                = config["warmup_steps"],
        learning_rate               = config["learning_rate"],
        weight_decay                = config["weight_decay"],
        lr_scheduler_type           = config["lr_scheduler_type"],
        fp16                        = True,
        bf16                        = False,
        logging_steps               = 10,
        eval_strategy               = "epoch",
        save_strategy               = "no",
        report_to                   = "none",
        seed                        = 42,
        optim                       = "paged_adamw_8bit",
        dataloader_pin_memory       = False,   # reduce VRAM overhead pe Kaggle
    )

    # ── 6. SFTTrainer ─────────────────────────────────────────
    trainer = SFTTrainer(
        model           = model,
        args            = training_args,
        train_dataset   = train_ds,
        eval_dataset    = val_ds,
        processing_class= tokenizer,
        dataset_text_field = "text",
        max_seq_length  = config["max_seq_length"],
        packing         = False,
    )

    # ── 7. Training ───────────────────────────────────────────
    print("🚀 Training start...")
    t_start = time.time()
    trainer.train()
    t_end   = time.time()

    training_minutes = round((t_end - t_start) / 60, 2)
    config["training_time_minutes"] = training_minutes
    print(f"✅ Training terminat în {training_minutes} min")

    # ── 8. Elibereaza trainer inainte de evaluare ─────────────
    del trainer, train_ds, val_ds
    gc.collect()
    torch.cuda.empty_cache()

    # ── 9. Evaluare ───────────────────────────────────────────
    metrics, preds = evaluate_model(model, tokenizer, test_data, run_name)
    metrics["training_time_minutes"] = training_minutes
    metrics["config"] = config
    all_metrics.append(metrics)

    # ── 10. Salvare ───────────────────────────────────────────
    local_path = save_run(model, tokenizer, config, metrics, preds, run_name)
    push_to_hf(local_path, run_name)
    append_global_metrics(metrics, run_name)

    # ── 11. Elibereaza modelul complet ────────────────────────
    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()

    vram_free = torch.cuda.memory_reserved(0) / 1e9
    print(f"🧹 Memorie eliberată. VRAM rezervat: {vram_free:.1f} GB")
    torch.cuda.empty_cache()
    
# ── Final summary ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"✅ TOATE {len(CONFIGS)} RUNS COMPLETE!")
print(f"{'='*60}")
print(f"\n🏆 Sumar rezultate:")
for m in sorted(all_metrics, key=lambda x: x.get("codebleu", 0), reverse=True):
    print(f"   {m['run_name']:35s} | CodeBLEU: {m['codebleu']:.4f} | ROUGE-L: {m['rougeL']:.4f}")