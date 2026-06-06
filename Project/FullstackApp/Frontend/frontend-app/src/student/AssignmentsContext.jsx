import { createContext, useContext, useState } from "react";
import { CLASSES, ASSIGNMENTS } from "./mockData";

// Deep-clone initial data so mutations don't touch the imported constants
function buildInitial() {
  const map = {};
  CLASSES.forEach(cls => {
    map[cls.id] = (ASSIGNMENTS[cls.id] ?? []).map(a => ({ ...a, submission: null }));
  });
  return map;
}

const Ctx = createContext(null);

export function AssignmentsProvider({ children }) {
  const [data, setData] = useState(buildInitial);

  function submit(classId, assignmentId, files) {
    const date = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    setData(prev => ({
      ...prev,
      [classId]: prev[classId].map(a =>
        a.id === assignmentId
          ? { ...a, status: "submitted", submission: { files, date } }
          : a
      ),
    }));
  }

  function unsubmit(classId, assignmentId) {
    setData(prev => ({
      ...prev,
      [classId]: prev[classId].map(a =>
        a.id === assignmentId
          ? { ...a, status: "pending", submission: null }
          : a
      ),
    }));
  }

  // Returns flat list with cls attached, optional filter by status
  function allAssignments() {
    return CLASSES.flatMap(cls =>
      (data[cls.id] ?? []).map(a => ({ ...a, cls }))
    );
  }

  function classAssignments(classId) {
    return data[classId] ?? [];
  }

  return (
    <Ctx.Provider value={{ data, submit, unsubmit, allAssignments, classAssignments }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAssignments() {
  return useContext(Ctx);
}
