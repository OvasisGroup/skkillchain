// Shared "first + last, fallback to email" convention used anywhere a
// person's name might not be set yet (profile.first_name/last_name are
// optional at signup).
export function displayName(person: { first_name: string; last_name: string; email: string }): string {
  const name = `${person.first_name} ${person.last_name}`.trim();
  return name || person.email;
}
