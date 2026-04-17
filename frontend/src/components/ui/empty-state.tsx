import { Card, CardDescription, CardTitle } from "@/components/ui/card";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="border-dashed bg-white/60 text-center">
      <CardTitle>{title}</CardTitle>
      <CardDescription className="mt-2">{description}</CardDescription>
    </Card>
  );
}
