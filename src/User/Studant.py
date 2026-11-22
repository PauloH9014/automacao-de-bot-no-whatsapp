class Student:
    def __init__(self, name, telephone):
        self.validate_student_nulo(name)
        self.validate_student_empty(name)
        if telephone == "":
            raise ValueError("Student telephone cannot be empty.")

        self._name = name
        self._telephone = telephone

    def validate_student_nulo(self, name):
        if name is None:
            raise ValueError("Student name cannot be null.")

    def validate_student_empty(self, name):
        if name == "":
            raise ValueError("Student name cannot be empty.")

    def get_name(self):
        return self._name

    def get_telephone(self):
        return self._telephone