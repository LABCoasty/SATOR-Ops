export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* TODO: Add mode switcher header and navigation */}
      <main>{children}</main>
    </div>
  );
}
