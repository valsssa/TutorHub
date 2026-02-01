import { ReactNode } from "react";
import PageLayout from "@/components/PageLayout";

interface PublicLayoutProps {
  children: ReactNode;
}

export default function PublicLayout({ children }: PublicLayoutProps) {
  return (
    <PageLayout showHeader={true} showFooter={true}>
      {children}
    </PageLayout>
  );
}