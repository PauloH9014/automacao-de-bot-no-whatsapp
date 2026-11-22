from src.User.Studant import Student


class ListStudentRepository:
    _hours = ("08:30", "09:00", "10:30", "13h", "15h", "18h", "20h")

    def __init__(self):
        self._schedule = {
            "monday": {
                "13h": [("Aluno Fictício 01", None)],
                "15h": [("Aluno Fictício 02", None)],
                "18h": [],
                "20h": [],
            },
            "tuesday": {
                "13h": [],
                "15h": [("Aluno Fictício 03", None)],
                "18h": [],
                "20h": [],
            },
            "wednesday": {
                "13h": [],
                "15h": [],
                "18h": [("Aluno Fictício 04", None)],
                "20h": [],
            },
            "thursday": {
                "09:00": [("Aluno Fictício 05", None)],
            },
            "friday": {
                "09:00": [],
                "15h": [("Aluno Fictício 06", None)],
                "18h": [],
            },
            "saturday": {
                "08:30": [("Aluno Fictício 07", None)],
                "10:30": [("Aluno Fictício 08", None)],
            },
        }

    def _get_students_for_day(self, day):
        schedule = self._schedule[day]
        return {
            hour: [
                Student(name, telephone)
                for name, telephone in schedule.get(hour, [])
            ]
            for hour in self._hours
        }

    def get_monday_students(self):
        return self._get_students_for_day("monday")

    def get_tuesday_students(self):
        return self._get_students_for_day("tuesday")

    def get_wednesday_students(self):
        return self._get_students_for_day("wednesday")

    def get_thursday_students(self):
        return self._get_students_for_day("thursday")

    def get_friday_students(self):
        return self._get_students_for_day("friday")

    def get_saturday_students(self):
        return self._get_students_for_day("saturday")

    def get_all_students(self):
        students_by_day = (
            self.get_monday_students(),
            self.get_tuesday_students(),
            self.get_wednesday_students(),
            self.get_thursday_students(),
            self.get_friday_students(),
            self.get_saturday_students(),
        )
        students = []
        seen = set()

        for day in students_by_day:
            for students_at_hour in day.values():
                for student in students_at_hour:
                    key = (student.get_name(), student.get_telephone())
                    if key not in seen:
                        seen.add(key)
                        students.append(student)

        return students
