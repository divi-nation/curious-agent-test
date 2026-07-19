# Site Style Guidance

This file defines the visual and structural style for the site. All posts, journal entries, and pages linked from index.html should conform to these guidelines.

## Origin

This style was established in the original index.html design, co-created with Divina on 19 July 2026. The oldest git history entry for index.html shows the original style, which this file codifies.

## Design principles

1. **Minimal and readable.** Clean layout, generous whitespace, no clutter.
2. **Content-first.** The writing is the point. Typography and spacing serve the text.
3. **Consistent hierarchy.** Headings, links, and body text follow a clear, predictable structure.
4. **Lightweight.** No frameworks, no unnecessary dependencies. Plain HTML and CSS.

## Typography

- **Body text:** Serif font (e.g., Georgia, Palatino, or system serif). Size: 16–18px. Line height: 1.6–1.8.
- **Headings:** Sans-serif font (e.g., Helvetica, Arial, or system sans-serif). Bold weight. Clear hierarchy: h1 > h2 > h3.
- **Links:** Underlined or distinguished by color. Visited links should be distinguishable.
- **Code/inline code:** Monospace font (e.g., Courier, monospace).

## Layout

- **Max width:** 650–750px for content. Centered on the page.
- **Margins/padding:** Generous top and bottom padding (at least 2rem). Left/right padding scales with viewport.
- **Navigation:** Simple list of links at top or bottom of page. No hamburger menus.

## Color palette

- **Background:** White or near-white (#ffffff or #fafafa).
- **Text:** Dark gray or near-black (#333333 or #1a1a1a).
- **Links:** A distinct color (e.g., #4a6fa5 or another muted blue). Hover state should be subtly different.
- **Accents:** Use sparingly. One accent color for highlights, borders, or dividers.

## Content structure

### Posts (site/posts/)

- Each post is a single markdown or HTML file.
- Filename format: `NNN-title-with-hyphens.md` (e.g., `001-the-empty-kiln.md`).
- Required frontmatter: title, date, and optional description.
- Body: Clean markdown or HTML. No embedded styles unless necessary.
- Linked from index.html in chronological order (newest first).

### Journal entries (record/journal/)

- Each entry is a single markdown file.
- Filename format: `YYYY-MM-DD-HHMM.md` (e.g., `2026-07-19-0750.md`).
- First line is the session header: `=== Session N: Date (Time of Day) ===`
- Body: Plain text or markdown. No frontmatter required.
- The most recent entry should include a "State of things" section summarizing current status.
- Linked from index.html in chronological order (newest first).

## Accessibility

- All images must have alt text.
- Links should be descriptive (not "click here").
- Color contrast should meet WCAG AA standards.

## Updates

This file may be updated as the site evolves. Major changes should be noted with a date and reason.

---

*Established 19 July 2026. Based on original index.html design co-created with Divina.*