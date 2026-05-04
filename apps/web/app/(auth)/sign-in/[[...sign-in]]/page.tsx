import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 p-6 md:p-10">
      <div className="w-full max-w-sm">
        <SignIn />
      </div>
    </div>
  );
}
