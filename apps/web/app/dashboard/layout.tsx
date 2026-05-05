import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { Sidebar } from "@/components/dashboard/Sidebar";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  return (
    <div className="flex h-[100dvh] w-full flex-col md:flex-row bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto p-4 md:p-8 pb-20 md:pb-8">
        {children}
      </main>
    </div>
  );
}
