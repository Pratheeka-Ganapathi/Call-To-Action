import type { ContentAnalysis } from "@/types/analysis"

type AnalyzeInput =
  | { kind: "file"; files: File[] }
  | { kind: "text"; text: string }

export async function analyzeContent(
  input: AnalyzeInput,
): Promise<ContentAnalysis> {
  await new Promise((resolve) => setTimeout(resolve, 2000))

  let title: string
  if (input.kind === "file") {
    title =
      input.files.length === 1
        ? `Analysis of ${input.files[0].name}`
        : `Combined analysis of ${input.files.length} files`
  } else {
    title = "Analysis of pasted text"
  }

  return {
    metadata: {
      title,
      content_type: "article",
    },
    summary: {
      main_point:
        "Products succeed by reliably doing a customer's job, not by stacking features.",
      key_takeaways: [
        "Customers hire products to do specific jobs, not for features.",
        "Competition includes anything else that does the same job.",
        "Features only matter if they make the job easier or faster.",
        "Customer interviews should focus on past job-hiring behavior.",
      ],
    },
    cta: {
      headline: "Apply Jobs-to-be-Done This Week",
      action_items: [
        "Write your product's core job in one sentence starting with a verb.",
        "List three non-obvious competitors that solve the same job.",
        "Audit your roadmap — flag features that don't map to the core job.",
      ],
      decisions_to_make: [
        "Should we redefine our core job statement formally across the team?",
      ],
      questions_to_explore: [
        "What unspoken needs are driving customers to hire our product?",
      ],
    },
  }
}