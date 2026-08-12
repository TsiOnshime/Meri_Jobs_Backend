package enrichment

import "strings"

// Seniority levels, ordered from least to most senior. Kept as
// constants so job-ingestion and any consumer agree on the exact
// strings used on the wire.
const (
	SeniorityJunior = "junior"
	SeniorityMid    = "mid"
	SenioritySenior = "senior"
	SeniorityLead   = "lead"
)

// Role categories. Anything that doesn't match a known keyword falls
// back to RoleCategoryOther rather than being left empty, so
// matching-engine always has a value to filter/group on.
const (
	RoleBackend   = "backend"
	RoleFrontend  = "frontend"
	RoleFullstack = "fullstack"
	RoleMobile    = "mobile"
	RoleDevOps    = "devops"
	RoleData      = "data"
	RoleDesign    = "design"
	RoleProduct   = "product"
	RoleQA        = "qa"
	RoleOther     = "other"
)

// minExperienceBySeniority is the heuristic mapping from seniority
// level to an assumed minimum years of experience. These numbers are a
// starting point, not a hiring policy -- easy to tune in one place.
var minExperienceBySeniority = map[string]int{
	SeniorityJunior: 0,
	SeniorityMid:    2,
	SenioritySenior: 5,
	SeniorityLead:   8,
}

// seniorityKeywords maps a lowercase substring found in the title to
// the seniority it implies. Checked in order; the first match wins,
// with the most specific/senior terms listed first so e.g. "Senior
// Staff Engineer" resolves to lead rather than senior.
var seniorityKeywords = []struct {
	keyword   string
	seniority string
}{
	{"principal", SeniorityLead},
	{"staff", SeniorityLead},
	{"lead", SeniorityLead},
	{"head of", SeniorityLead},
	{"director", SeniorityLead},
	{"senior", SenioritySenior},
	{"sr.", SenioritySenior},
	{"sr ", SenioritySenior},
	{"junior", SeniorityJunior},
	{"jr.", SeniorityJunior},
	{"jr ", SeniorityJunior},
	{"entry level", SeniorityJunior},
	{"intern", SeniorityJunior},
	{"graduate", SeniorityJunior},
}

// roleKeywords maps a lowercase substring to a role category. Checked
// in order; fullstack is listed before backend/frontend so "Full Stack
// Backend Engineer"-style titles land on fullstack rather than backend.
var roleKeywords = []struct {
	keyword string
	role    string
}{
	{"full stack", RoleFullstack},
	{"full-stack", RoleFullstack},
	{"fullstack", RoleFullstack},
	{"backend", RoleBackend},
	{"back end", RoleBackend},
	{"back-end", RoleBackend},
	{"frontend", RoleFrontend},
	{"front end", RoleFrontend},
	{"front-end", RoleFrontend},
	{"ios", RoleMobile},
	{"android", RoleMobile},
	{"mobile", RoleMobile},
	{"devops", RoleDevOps},
	{"sre", RoleDevOps},
	{"site reliability", RoleDevOps},
	{"infrastructure", RoleDevOps},
	{"platform engineer", RoleDevOps},
	{"data scientist", RoleData},
	{"data engineer", RoleData},
	{"machine learning", RoleData},
	{"ml engineer", RoleData},
	{"analytics", RoleData},
	{"designer", RoleDesign},
	{"ux", RoleDesign},
	{"ui", RoleDesign},
	{"product manager", RoleProduct},
	{"product owner", RoleProduct},
	{"qa", RoleQA},
	{"quality assurance", RoleQA},
	{"test engineer", RoleQA},
	{"sdet", RoleQA},
}

// Result holds the fields derived for a single job.
type Result struct {
	RequiredSkills []string
	MinExperience  int
	SeniorityLevel string
	RoleCategory   string
}

// Derive computes enrichment fields from a job's title and the tags
// its provider returned (used directly as RequiredSkills -- RemoteOK's
// tags are already a reasonable skills list).
func Derive(title string, tags []string) Result {
	lowerTitle := strings.ToLower(title)

	seniority := detectSeniority(lowerTitle)
	role := detectRole(lowerTitle)

	return Result{
		RequiredSkills: normalizeSkills(tags),
		MinExperience:  minExperienceBySeniority[seniority],
		SeniorityLevel: seniority,
		RoleCategory:   role,
	}
}

func detectSeniority(lowerTitle string) string {
	for _, sk := range seniorityKeywords {
		if strings.Contains(lowerTitle, sk.keyword) {
			return sk.seniority
		}
	}
	return SeniorityMid
}

func detectRole(lowerTitle string) string {
	for _, rk := range roleKeywords {
		if strings.Contains(lowerTitle, rk.keyword) {
			return rk.role
		}
	}
	return RoleOther
}

// normalizeSkills trims and lowercases provider tags, drops empties,
// and de-duplicates while preserving order -- so "React", "react " and
// "REACT" collapse to one entry.
func normalizeSkills(tags []string) []string {
	seen := make(map[string]bool, len(tags))
	out := make([]string, 0, len(tags))
	for _, t := range tags {
		clean := strings.ToLower(strings.TrimSpace(t))
		if clean == "" || seen[clean] {
			continue
		}
		seen[clean] = true
		out = append(out, clean)
	}
	return out
}
