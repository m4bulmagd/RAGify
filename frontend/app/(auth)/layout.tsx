export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen w-full items-center justify-center p-4 relative overflow-hidden">      
      <div className="relative w-full max-w-md">
        {children}
      </div>
    </div>
  )
}
