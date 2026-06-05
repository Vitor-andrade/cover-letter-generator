// The structured background editor: 9 sections behind a tab strip. The parent
// owns the Sections object; every edit produces a NEW object (mirroring the
// backend's whole-object reassignment) so React re-renders cleanly.
import { useState } from "react";
import type {
  CertificationEntry,
  EducationEntry,
  ExperienceEntry,
  LanguageEntry,
  ProjectEntry,
  Sections,
} from "./api";
import { ChipsInput, Field, ListEditor, SectionTabs, type TabDef } from "./ui";

export function emptySections(): Sections {
  return {
    contact: { email: "", phone: "", linkedin: "", location: "", website: "" },
    summary: "",
    key_skills: [],
    skills: [],
    experiences: [],
    projects: [],
    education: [],
    certifications: [],
    languages: [],
  };
}

const blankExperience = (): ExperienceEntry => ({
  role: "",
  company: "",
  period: "",
  location: "",
  highlights: [],
});
const blankProject = (): ProjectEntry => ({
  name: "",
  description: "",
  tech: [],
  highlights: [],
  link: "",
});
const blankEducation = (): EducationEntry => ({ degree: "", institution: "", period: "", details: "" });
const blankCertification = (): CertificationEntry => ({ name: "", issuer: "", year: "" });
const blankLanguage = (): LanguageEntry => ({ language: "", proficiency: "" });

type SectionKey = keyof Sections;

const TABS: { key: SectionKey; label: string }[] = [
  { key: "contact", label: "Contact" },
  { key: "summary", label: "Summary" },
  { key: "key_skills", label: "Key skills" },
  { key: "skills", label: "Skills" },
  { key: "experiences", label: "Experience" },
  { key: "projects", label: "Projects" },
  { key: "education", label: "Education" },
  { key: "certifications", label: "Certifications" },
  { key: "languages", label: "Languages" },
];

function isFilled(sections: Sections, key: SectionKey): boolean {
  const v = sections[key];
  if (key === "contact") return Object.values(sections.contact).some((s) => s.trim());
  if (key === "summary") return sections.summary.trim().length > 0;
  return Array.isArray(v) && v.length > 0;
}

export function hasAnyContent(sections: Sections): boolean {
  return TABS.some((t) => isFilled(sections, t.key));
}

export function SectionsEditor({
  sections,
  onChange,
}: {
  sections: Sections;
  onChange: (next: Sections) => void;
}) {
  const [active, setActive] = useState<SectionKey>("contact");
  const set = <K extends SectionKey>(key: K, value: Sections[K]) =>
    onChange({ ...sections, [key]: value });
  const setContact = (patch: Partial<Sections["contact"]>) =>
    onChange({ ...sections, contact: { ...sections.contact, ...patch } });

  const tabs: TabDef[] = TABS.map((t) => ({ ...t, filled: isFilled(sections, t.key) }));

  return (
    <div className="sections-editor">
      <SectionTabs tabs={tabs} active={active} onSelect={(k) => setActive(k as SectionKey)} />

      {active === "contact" && (
        <div className="row">
          <Field label="Email">
            <input className="input" value={sections.contact.email} onChange={(e) => setContact({ email: e.target.value })} placeholder="jane@example.com" />
          </Field>
          <Field label="Phone">
            <input className="input" value={sections.contact.phone} onChange={(e) => setContact({ phone: e.target.value })} placeholder="+1 555 0100" />
          </Field>
          <Field label="LinkedIn">
            <input className="input" value={sections.contact.linkedin} onChange={(e) => setContact({ linkedin: e.target.value })} placeholder="linkedin.com/in/jane" />
          </Field>
          <Field label="Location">
            <input className="input" value={sections.contact.location} onChange={(e) => setContact({ location: e.target.value })} placeholder="Berlin, Germany" />
          </Field>
          <Field label="Website">
            <input className="input" value={sections.contact.website} onChange={(e) => setContact({ website: e.target.value })} placeholder="https://jane.dev" />
          </Field>
        </div>
      )}

      {active === "summary" && (
        <Field label="Professional summary">
          <textarea className="textarea" value={sections.summary} onChange={(e) => set("summary", e.target.value)} placeholder="Backend engineer with 12 years building…" />
        </Field>
      )}

      {active === "key_skills" && (
        <Field label="Key skills (your strongest, highlighted)">
          <ChipsInput values={sections.key_skills} onChange={(v) => set("key_skills", v)} placeholder="Add a key skill…" />
        </Field>
      )}

      {active === "skills" && (
        <Field label="Skills">
          <ChipsInput values={sections.skills} onChange={(v) => set("skills", v)} placeholder="Add a skill…" />
        </Field>
      )}

      {active === "experiences" && (
        <ListEditor
          items={sections.experiences}
          onChange={(v) => set("experiences", v)}
          blank={blankExperience}
          addLabel="+ Add experience"
          renderItem={(item, update) => (
            <>
              <div className="row">
                <Field label="Role"><input className="input" value={item.role} onChange={(e) => update({ role: e.target.value })} placeholder="Staff Engineer" /></Field>
                <Field label="Company"><input className="input" value={item.company} onChange={(e) => update({ company: e.target.value })} placeholder="Acme" /></Field>
              </div>
              <div className="row">
                <Field label="Period"><input className="input" value={item.period} onChange={(e) => update({ period: e.target.value })} placeholder="2020 – now" /></Field>
                <Field label="Location"><input className="input" value={item.location} onChange={(e) => update({ location: e.target.value })} placeholder="Remote" /></Field>
              </div>
              <Field label="Highlights"><ChipsInput values={item.highlights} onChange={(v) => update({ highlights: v })} placeholder="Add a highlight…" /></Field>
            </>
          )}
        />
      )}

      {active === "projects" && (
        <ListEditor
          items={sections.projects}
          onChange={(v) => set("projects", v)}
          blank={blankProject}
          addLabel="+ Add project"
          renderItem={(item, update) => (
            <>
              <div className="row">
                <Field label="Name"><input className="input" value={item.name} onChange={(e) => update({ name: e.target.value })} placeholder="Ledger" /></Field>
                <Field label="Link"><input className="input" value={item.link} onChange={(e) => update({ link: e.target.value })} placeholder="https://github.com/…" /></Field>
              </div>
              <Field label="Description"><textarea className="textarea" value={item.description} onChange={(e) => update({ description: e.target.value })} placeholder="Double-entry accounting library" /></Field>
              <Field label="Tech"><ChipsInput values={item.tech} onChange={(v) => update({ tech: v })} placeholder="Add a technology…" /></Field>
              <Field label="Highlights"><ChipsInput values={item.highlights} onChange={(v) => update({ highlights: v })} placeholder="Add a highlight…" /></Field>
            </>
          )}
        />
      )}

      {active === "education" && (
        <ListEditor
          items={sections.education}
          onChange={(v) => set("education", v)}
          blank={blankEducation}
          addLabel="+ Add education"
          renderItem={(item, update) => (
            <>
              <div className="row">
                <Field label="Degree"><input className="input" value={item.degree} onChange={(e) => update({ degree: e.target.value })} placeholder="MSc Computer Science" /></Field>
                <Field label="Institution"><input className="input" value={item.institution} onChange={(e) => update({ institution: e.target.value })} placeholder="UCL" /></Field>
              </div>
              <Field label="Period"><input className="input" value={item.period} onChange={(e) => update({ period: e.target.value })} placeholder="2008 – 2010" /></Field>
              <Field label="Details"><textarea className="textarea" value={item.details} onChange={(e) => update({ details: e.target.value })} placeholder="Thesis, honors, relevant coursework…" /></Field>
            </>
          )}
        />
      )}

      {active === "certifications" && (
        <ListEditor
          items={sections.certifications}
          onChange={(v) => set("certifications", v)}
          blank={blankCertification}
          addLabel="+ Add certification"
          renderItem={(item, update) => (
            <div className="row">
              <Field label="Name"><input className="input" value={item.name} onChange={(e) => update({ name: e.target.value })} placeholder="CKA" /></Field>
              <Field label="Issuer"><input className="input" value={item.issuer} onChange={(e) => update({ issuer: e.target.value })} placeholder="CNCF" /></Field>
              <Field label="Year"><input className="input" value={item.year} onChange={(e) => update({ year: e.target.value })} placeholder="2022" /></Field>
            </div>
          )}
        />
      )}

      {active === "languages" && (
        <ListEditor
          items={sections.languages}
          onChange={(v) => set("languages", v)}
          blank={blankLanguage}
          addLabel="+ Add language"
          renderItem={(item, update) => (
            <div className="row">
              <Field label="Language"><input className="input" value={item.language} onChange={(e) => update({ language: e.target.value })} placeholder="English" /></Field>
              <Field label="Proficiency"><input className="input" value={item.proficiency} onChange={(e) => update({ proficiency: e.target.value })} placeholder="Native" /></Field>
            </div>
          )}
        />
      )}
    </div>
  );
}
