"""API schemas for the Skills resource (Phase 3 section 59).

Serializes domain.skills.entities.Skill and
domain.skills.relationships.SkillRelationshipView directly - these are
plain framework-free dataclasses, not Django models, so plain
serializers.Serializer classes are used rather than ModelSerializer.
"""
from rest_framework import serializers

from domain.skills.enums import skill_domain_for_category


class SkillRefSerializer(serializers.Serializer):
    """A lightweight reference to a skill - used wherever another skill
    is embedded (parent, children, ecosystem siblings, relations) so the
    response never needs to recurse into a skill's own relationships.
    """

    canonical_name = serializers.CharField()
    category = serializers.CharField()
    domain = serializers.SerializerMethodField()
    description = serializers.CharField(allow_null=True)

    def get_domain(self, skill) -> str:
        return skill_domain_for_category(skill.category).value


class RelatedSkillSerializer(serializers.Serializer):
    skill = SkillRefSerializer()
    relation_type = serializers.CharField()


class SkillDetailSerializer(serializers.Serializer):
    """Built from a domain.skills.relationships.SkillRelationshipView,
    not a bare Skill - `view.skill` is the subject, everything else is
    its derived/explicit relationships (see build_relationship_view).
    """

    canonical_name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    aliases = serializers.SerializerMethodField()
    ecosystem = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    parent = SkillRefSerializer(allow_null=True)
    children = SkillRefSerializer(many=True)
    ecosystem_siblings = SkillRefSerializer(many=True)
    explicit = RelatedSkillSerializer(many=True)

    def get_canonical_name(self, view) -> str:
        return view.skill.canonical_name

    def get_category(self, view) -> str:
        return view.skill.category.value

    def get_domain(self, view) -> str:
        return skill_domain_for_category(view.skill.category).value

    def get_aliases(self, view) -> list[str]:
        return list(view.skill.aliases)

    def get_ecosystem(self, view) -> str | None:
        return view.skill.ecosystem

    def get_description(self, view) -> str | None:
        return view.skill.description
