"use client";

import FinsightChat from '@/components/finsight';
import { useUser } from '@clerk/nextjs';

export default function FinsightPage() {
  const { user } = useUser();
  const userId = user?.id || 'anonymous';
  
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <FinsightChat userId={userId} />
    </div>
  );
}
