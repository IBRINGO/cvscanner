from domain.cv.education_normalization import EducationLevel, normalize_education_level


class TestNormalizeEducationLevel:
    def test_recognizes_bachelor_variants(self):
        assert normalize_education_level("Bachelor of Science in Computer Science") == EducationLevel.BACHELOR
        assert normalize_education_level("BSc Computer Science") == EducationLevel.BACHELOR
        assert normalize_education_level("Licence en informatique") == EducationLevel.BACHELOR

    def test_recognizes_master_variants(self):
        assert normalize_education_level("Master of Business Administration") == EducationLevel.MASTER
        assert normalize_education_level("MSc Data Science") == EducationLevel.MASTER

    def test_recognizes_doctorate_before_master_false_match(self):
        assert normalize_education_level("PhD in Computer Science") == EducationLevel.DOCTORATE

    def test_recognizes_high_school(self):
        assert normalize_education_level("High School Diploma") == EducationLevel.HIGH_SCHOOL

    def test_recognizes_professional_certificate(self):
        assert normalize_education_level("AWS Certification") == EducationLevel.PROFESSIONAL_CERTIFICATE

    def test_unrecognized_wording_is_unknown(self):
        assert normalize_education_level("Some Obscure Program") == EducationLevel.UNKNOWN

    def test_none_and_empty_are_unknown(self):
        assert normalize_education_level(None) == EducationLevel.UNKNOWN
        assert normalize_education_level("") == EducationLevel.UNKNOWN
