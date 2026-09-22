from domain.cv.seniority import SeniorityLevel, normalize_seniority


class TestNormalizeSeniority:
    def test_recognizes_senior(self):
        assert normalize_seniority("Senior Software Engineer") == SeniorityLevel.SENIOR

    def test_recognizes_junior_and_its_abbreviation(self):
        assert normalize_seniority("Junior Developer") == SeniorityLevel.JUNIOR
        assert normalize_seniority("Jr. Developer") == SeniorityLevel.JUNIOR

    def test_recognizes_lead_and_staff_and_principal(self):
        assert normalize_seniority("Tech Lead") == SeniorityLevel.LEAD
        assert normalize_seniority("Staff Engineer") == SeniorityLevel.LEAD
        assert normalize_seniority("Principal Engineer") == SeniorityLevel.LEAD

    def test_recognizes_manager(self):
        assert normalize_seniority("Engineering Manager") == SeniorityLevel.MANAGER

    def test_recognizes_director(self):
        assert normalize_seniority("Director of Engineering") == SeniorityLevel.DIRECTOR

    def test_recognizes_executive_titles(self):
        assert normalize_seniority("Chief Technology Officer") == SeniorityLevel.EXECUTIVE
        assert normalize_seniority("VP of Engineering") == SeniorityLevel.EXECUTIVE

    def test_recognizes_intern(self):
        assert normalize_seniority("Software Engineering Intern") == SeniorityLevel.INTERN

    def test_more_specific_role_wins_over_generic_senior_modifier(self):
        assert normalize_seniority("Senior Engineering Manager") == SeniorityLevel.MANAGER

    def test_plain_title_with_no_keyword_is_unknown_not_guessed(self):
        assert normalize_seniority("Software Engineer") == SeniorityLevel.UNKNOWN

    def test_none_and_empty_are_unknown(self):
        assert normalize_seniority(None) == SeniorityLevel.UNKNOWN
        assert normalize_seniority("") == SeniorityLevel.UNKNOWN
