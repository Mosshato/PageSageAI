export const CLASSES = [
  { id: 1, name: "Mathematics", teacher: "Mr. Anderson", code: "MATH101", color: "#f97316", icon: "∑", pending: 2 },
  { id: 2, name: "Physics", teacher: "Dr. Carter", code: "PHY202", color: "#3b82f6", icon: "⚛", pending: 1 },
  { id: 3, name: "Literature", teacher: "Ms. Bennett", code: "LIT303", color: "#8b5cf6", icon: "✦", pending: 0 },
  { id: 4, name: "Computer Science", teacher: "Prof. Walsh", code: "CS404", color: "#10b981", icon: "</>", pending: 3 },
];

export const ANNOUNCEMENTS = {
  1: [
    { id: 1, author: "Mr. Anderson", avatar: "A", date: "May 8", text: "Reminder: Problem Set 4 is due tomorrow. Make sure to show all your work for full credit. Office hours are available this afternoon from 3–5pm if you need help.", pinned: true },
    { id: 2, author: "Mr. Anderson", avatar: "A", date: "May 5", text: "Great job on the midterm everyone! Grades have been posted. The class average was 84%. We'll review the most common mistakes in Thursday's lecture.", pinned: false },
    { id: 3, author: "Mr. Anderson", avatar: "A", date: "Apr 30", text: "Chapter 7 notes have been uploaded to the Materials section. Please read pages 120–145 before our next class.", pinned: false },
  ],
  2: [
    { id: 1, author: "Dr. Carter", avatar: "C", date: "May 7", text: "Lab session this Friday will be in Room 204 instead of the usual lab. Bring your lab notebooks and safety goggles.", pinned: true },
    { id: 2, author: "Dr. Carter", avatar: "C", date: "May 3", text: "The Chapter 5 Quiz has been scheduled for next Tuesday. It will cover thermodynamics and wave mechanics.", pinned: false },
  ],
  3: [
    { id: 1, author: "Ms. Bennett", avatar: "B", date: "May 6", text: "Essay drafts are due by end of week. Submit via the Assignments tab. I'll return feedback within 5 business days.", pinned: false },
  ],
  4: [
    { id: 1, author: "Prof. Walsh", avatar: "W", date: "May 8", text: "Lab Assignment 2 is now live — check the Assignments tab. You have until Friday. Start early, the recursive section takes time to debug.", pinned: true },
    { id: 2, author: "Prof. Walsh", avatar: "W", date: "May 6", text: "Project Proposal deadline extended to May 15th. Groups of 2–3 students. Topic must be approved before you start building.", pinned: false },
    { id: 3, author: "Prof. Walsh", avatar: "W", date: "May 1", text: "Office hours moved to Wednesday 2–4pm this week. Come with questions about the midterm project.", pinned: false },
  ],
};

export const ASSIGNMENTS = {
  1: [
    { id: 1, title: "Problem Set 4", due: "May 9", status: "pending", points: 100, description: "Solve all problems in Chapter 6. Show all work for full credit.", attachments: [{ name: "chapter6_problems.pdf" }, { name: "formula_sheet.pdf" }] },
    { id: 4, title: "Chapter 7 Review", due: "May 14", status: "pending", points: 60, description: "Review exercises for Chapter 7. Focus on integration techniques.", attachments: [{ name: "chapter7_review.pdf" }] },
    { id: 2, title: "Problem Set 3", due: "Apr 28", status: "submitted", points: 100, grade: 92, description: "Chapter 5 problems.", attachments: [] },
    { id: 3, title: "Midterm Exam", due: "Apr 15", status: "graded", points: 200, grade: 84, description: "Covers chapters 1–4.", attachments: [{ name: "midterm_study_guide.pdf" }] },
  ],
  2: [
    { id: 1, title: "Chapter 5 Quiz", due: "May 14", status: "pending", points: 50, description: "Thermodynamics and wave mechanics. Open notes.", attachments: [{ name: "thermo_notes.pdf" }, { name: "wave_equations.docx" }] },
    { id: 2, title: "Lab Report 3", due: "May 3", status: "submitted", points: 80, description: "Write-up for the optics experiment.", attachments: [{ name: "lab3_template.docx" }, { name: "optics_data.xlsx" }] },
  ],
  3: [
    { id: 1, title: "Essay Draft", due: "May 10", status: "pending", points: 150, description: "800–1000 word draft on the assigned novel's themes.", attachments: [{ name: "essay_guidelines.pdf" }] },
    { id: 3, title: "Poetry Analysis", due: "May 14", status: "pending", points: 80, description: "Analyze the use of metaphor and rhythm in three assigned poems.", attachments: [{ name: "poems_collection.pdf" }, { name: "analysis_rubric.pdf" }] },
    { id: 2, title: "Reading Response 4", due: "Apr 25", status: "graded", points: 30, grade: 95, description: "One-page response to chapters 12–15.", attachments: [] },
  ],
  4: [
    { id: 1, title: "Lab Assignment 2", due: "May 12", status: "pending", points: 100, description: "Implement a recursive descent parser. Starter code in the repo.", attachments: [{ name: "starter_code.zip" }, { name: "parser_spec.pdf" }, { name: "test_cases.py" }] },
    { id: 2, title: "Project Proposal", due: "May 15", status: "pending", points: 50, description: "2-page proposal for your semester project. Groups of 2–3.", attachments: [{ name: "proposal_template.docx" }] },
    { id: 3, title: "Lab Assignment 1", due: "Apr 20", status: "graded", points: 100, grade: 88, description: "Linked list implementation.", attachments: [{ name: "lab1_starter.zip" }] },
  ],
};

export const LECTURES = {
  1: [
    { id: 1, title: "Introduction to Limits", date: "May 7", duration: "52 min", description: "Covers the intuitive and formal definition of a limit, one-sided limits, and limit laws.", files: [{ name: "limits_slides.pdf" }, { name: "limit_examples.pdf" }] },
    { id: 2, title: "Derivatives — Definition & Rules", date: "May 5", duration: "48 min", description: "Power rule, product rule, quotient rule with worked examples.", files: [{ name: "derivatives_slides.pdf" }] },
    { id: 3, title: "Chain Rule & Implicit Differentiation", date: "Apr 30", duration: "55 min", description: "Composite functions, implicit curves, and related rates.", files: [{ name: "chain_rule.pdf" }, { name: "practice_sheet.pdf" }] },
    { id: 4, title: "Integration Basics", date: "Apr 28", duration: "50 min", description: "Anti-derivatives, indefinite integrals, and the constant of integration.", files: [{ name: "integration_intro.pdf" }] },
  ],
  2: [
    { id: 1, title: "Newton's Laws of Motion", date: "May 6", duration: "45 min", description: "Free-body diagrams, net force, and applying all three laws to classic problems.", files: [{ name: "newtons_laws.pdf" }] },
    { id: 2, title: "Work, Energy & Power", date: "May 1", duration: "50 min", description: "Kinetic and potential energy, work-energy theorem, conservation of energy.", files: [{ name: "energy_slides.pdf" }, { name: "energy_problems.pdf" }] },
    { id: 3, title: "Waves & Oscillations", date: "Apr 25", duration: "58 min", description: "Simple harmonic motion, period, frequency, and standing waves.", files: [{ name: "waves_lecture.pdf" }] },
  ],
  3: [
    { id: 1, title: "Romanticism in European Poetry", date: "May 5", duration: "40 min", description: "Historical context, key themes, and close reading of Keats and Shelley.", files: [{ name: "romanticism_notes.pdf" }] },
    { id: 2, title: "Narrative Voice & Point of View", date: "Apr 29", duration: "38 min", description: "First vs third person, unreliable narrator, and free indirect discourse.", files: [{ name: "narrative_voice.pdf" }, { name: "reading_excerpts.pdf" }] },
    { id: 3, title: "Metaphor, Simile & Imagery", date: "Apr 22", duration: "42 min", description: "Figurative language devices with examples from the assigned texts.", files: [{ name: "figurative_language.pdf" }] },
  ],
  4: [
    { id: 1, title: "Recursion & Recursive Algorithms", date: "May 8", duration: "60 min", description: "Stack frames, base cases, tree recursion, and memoization strategies.", files: [{ name: "recursion_slides.pdf" }, { name: "recursion_exercises.zip" }] },
    { id: 2, title: "Data Structures — Linked Lists", date: "May 3", duration: "55 min", description: "Singly and doubly linked lists, insertion, deletion, and traversal.", files: [{ name: "linked_lists.pdf" }] },
    { id: 3, title: "Sorting Algorithms", date: "Apr 27", duration: "62 min", description: "Bubble, merge, and quicksort — complexity analysis and comparisons.", files: [{ name: "sorting_slides.pdf" }, { name: "sorting_viz.py" }] },
    { id: 4, title: "Introduction to Trees & Graphs", date: "Apr 21", duration: "58 min", description: "Binary trees, BST operations, BFS, and DFS traversal.", files: [{ name: "trees_graphs.pdf" }] },
  ],
};

export const CLASSMATES = {
  1: [
    { id: 1, name: "Alice Morgan", initials: "AM", color: "#f97316" },
    { id: 2, name: "Ben Carter", initials: "BC", color: "#3b82f6" },
    { id: 3, name: "Clara West", initials: "CW", color: "#8b5cf6" },
    { id: 4, name: "David Kim", initials: "DK", color: "#10b981" },
    { id: 5, name: "Eva Rossi", initials: "ER", color: "#ec4899" },
  ],
  2: [
    { id: 1, name: "Felix Nguyen", initials: "FN", color: "#eab308" },
    { id: 2, name: "Grace Liu", initials: "GL", color: "#10b981" },
    { id: 3, name: "Henry Park", initials: "HP", color: "#3b82f6" },
  ],
  3: [
    { id: 1, name: "Isla Thompson", initials: "IT", color: "#8b5cf6" },
    { id: 2, name: "Jack Brown", initials: "JB", color: "#f97316" },
  ],
  4: [
    { id: 1, name: "Karen White", initials: "KW", color: "#ec4899" },
    { id: 2, name: "Leo Martinez", initials: "LM", color: "#f97316" },
    { id: 3, name: "Mia Johansson", initials: "MJ", color: "#3b82f6" },
    { id: 4, name: "Noah Garcia", initials: "NG", color: "#10b981" },
    { id: 5, name: "Olivia Chen", initials: "OC", color: "#8b5cf6" },
    { id: 6, name: "Paul Adams", initials: "PA", color: "#eab308" },
  ],
};
