"use client";

import { useParams } from "next/navigation";

import { FichaSistema } from "@/components/ninja-dev/ficha-sistema";

export default function SistemaPage() {
  const params = useParams<{ id: string }>();
  return <FichaSistema id={Number(params?.id)} />;
}
