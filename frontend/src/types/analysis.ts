// Mirrors the Pydantic ContentAnalysis schema from the Python project.
// When the real backend is wired up later, the JSON it returns must
// match these shapes exactly.

export interface Metadata {
    title: string
    content_type: string
  }
  
  export interface Summary {
    main_point: string
    key_takeaways: string[]
  }
  
  export interface CallToAction {
    headline: string
    action_items: string[]
    decisions_to_make: string[]
    questions_to_explore: string[]
  }
  
  export interface ContentAnalysis {
    metadata: Metadata
    summary: Summary
    cta: CallToAction
  }

  export interface JobSummary {
    id: string
    created_at: string
    source_kind: string
    source_label: string
  }
  
  export interface JobDetail extends JobSummary {
    analysis: ContentAnalysis
  }