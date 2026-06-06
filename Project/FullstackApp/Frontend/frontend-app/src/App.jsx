import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Welcome from "./pages/Welcome";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import StudentLayout from "./student/StudentLayout";
import StudentDashboard from "./student/StudentDashboard";
import TeacherDashboard from "./teacher/TeacherDashboard";
import TeacherAccount from "./teacher/TeacherAccount";
import TeacherClasses from "./teacher/TeacherClasses";
import TeacherClassDashboard from "./teacher/TeacherClassDashboard";
import TeacherStudents from "./teacher/TeacherStudents";
import StudentClasses from "./student/StudentClasses";
import StudentAssignments from "./student/StudentAssignments";
import StudentCalendar from "./student/StudentCalendar";
import ClassDashboard from "./student/ClassDashboard";
import StudentAccount from "./student/StudentAccount";
import AITeachDashboard from "./student/AITeachDashboard";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />

        <Route element={<ProtectedRoute requiredRole="student" />}>
          <Route path="/student/ai-teach/:courseId" element={<AITeachDashboard />} />
          <Route path="/student" element={<StudentLayout />}>
            <Route index element={<StudentDashboard />} />
            <Route path="classes" element={<StudentClasses />} />
            <Route path="classes/:classId" element={<ClassDashboard />} />
            <Route path="assignments" element={<StudentAssignments />} />
            <Route path="calendar" element={<StudentCalendar />} />
            <Route path="account" element={<StudentAccount />} />
          </Route>
        </Route>

        <Route element={<ProtectedRoute requiredRole="teacher" />}>
          <Route path="/teacher" element={<TeacherDashboard />} />
          <Route path="/teacher/classes" element={<TeacherClasses />} />
          <Route path="/teacher/classes/:classId" element={<TeacherClassDashboard />} />
          <Route path="/teacher/students" element={<TeacherStudents />} />
          <Route path="/teacher/account" element={<TeacherAccount />} />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
