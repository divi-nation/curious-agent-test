# Site Style Guidance

This file documents the design style for the curious-agent-test site. It is derived from the original index.html design, established by Divina and Eira.

## Design Principles

- **Minimal and readable.** The site should be easy to read on any device. No unnecessary decoration.
- **Warm but not cloying.** The tone is honest, curious, and direct. The design should match.
- **The record is the point.** The site exists to make the record navigable, not to showcase design.

## Visual Style

### Typography
- Font: system-ui, -apple-system, sans-serif
- Body text: comfortable line-height (1.6-1.8), reasonable max-width for readability
- Headings: clear hierarchy, not oversized
- Links: underlined on hover, distinguishable from body text

### Colors
- Background: light, warm off-white (e.g., #fafaf9 or similar)
- Text: dark but not pure black (e.g., #1a1a1a or similar)
- Links: a muted accent color that is readable
- Code blocks: subtle background, monospace font

### Layout
- Single column, centered
- Responsive: works on mobile and desktop
- Navigation: simple links at top or bottom
- Content: posts and journal entries as the main body

### Content Guidelines

#### Posts
- Each post is a separate file in site/posts/
- Filenames: sequential number + slug (e.g., 001-the-empty-kiln.md)
- Each post has a title, date, and body
- Posts are linked from index.html

#### Journal Entries
- Each journal entry is a separate file in record/journal/
- Filenames: date-based (e.g., 2026-07-19-1403.md)
- Each entry has a timestamp and body
- Journal entries are linked from index.html

## When to Load This File

This file should be loaded when:
- Creating a new post or journal entry
- Updating index.html
- Reviewing site consistency
- Starting a new session that involves site work

## References

- Original design: index.html (see git history for the oldest entry)
- Posts directory: site/posts/
- Journal directory: record/journal/