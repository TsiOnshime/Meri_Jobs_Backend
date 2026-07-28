from django.core.management.base import BaseCommand
from matching.models import Skill, SkillAlias
from matching.skills.alias_resolver import refresh_alias_cache

SKILLS = {
    "python": ["python", "python3"],
    "django": ["django", "djangorestframework", "drf"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "docker": ["docker", "dockerized", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "redis": ["redis"],
    "kafka": ["kafka", "apache kafka"],
    "sql": ["sql"],
    "git": ["git", "github", "version control"],
    # add more as you identify them
}


class Command(BaseCommand):
    help = "Seeds the Skill and SkillAlias tables with an initial vocabulary."
    
    def handle(self, *args, **options):
        created_skills = 0
        created_aliases = 0
        
        for canonical_name, aliases in SKILLS.items():
            skill, was_created = Skill.objects.get_or_create(name=canonical_name)
            
            if was_created:
                created_skills += 1
            for alias_name in aliases:
                _, alias_created = SkillAlias.objects.get_or_create(
                    alias_name=alias_name,
                    defaults={"skill": skill}
                )
                if alias_created:
                    created_aliases += 1
        refresh_alias_cache()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_skills} skills, {created_aliases} aliases. Redis cache refreshed"
            )
        )