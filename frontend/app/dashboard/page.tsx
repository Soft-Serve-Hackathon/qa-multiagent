import { redirect } from 'next/navigation';

// The dashboard is now accessible as a tab at the root route (/).
// This redirect preserves backward compatibility with any bookmarks or
// documentation that references /dashboard directly.
export default function DashboardRedirect() {
  redirect('/');
}
