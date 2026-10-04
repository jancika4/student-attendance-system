CREATE DATABASE IF NOT EXISTS student_attendance;

USE student_attendance;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100),
    year INT
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id)
);
