import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface TaxDNA {
  visual_identity?: {
    primary_color?: string;
    secondary_color?: string;
    fonts?: string[];
    imagery_style?: string;
    confidence?: number;
  };
  verbal_identity?: {
    tone?: string;
    key_phrases?: string[];
    value_propositions?: string[];
    vocabulary_complexity?: string;
  };
  servicios?: Array<{
    name: string;
    description: string;
    price_model?: string;
    target_segments?: string[];
  }>;
  buyer_personas?: Array<{
    name: string;
    pain_points?: string[];
    goals?: string[];
    content_preferences?: string[];
    role?: string;
  }>;
  compliance_rules?: {
    forbidden_claims?: string[];
    required_disclaimers?: string[];
    dian_alignment?: string;
  };
  target_segments?: string[];
  differentiation?: {
    unique_selling_points?: string[];
    competitive_advantages?: string[];
    market_positioning?: string;
  };
}

export interface CampaignOption {
  name: string;
  type: 'instagram_calendar' | 'product_launch' | 'storytelling_series' | 'local_campaign' | 'retargeting';
  description?: string;
  duration_weeks?: number;
  total_posts?: number;
  expected_roi?: number;
  channels?: string[];
  budget_allocation?: number;
  recommended?: boolean;
}

export interface GeneratedPost {
  id?: string;
  fecha?: string;
  hora?: string;
  titulo?: string;
  contenido?: string;
  hashtags?: string[];
  cta?: string;
  canal?: string;
  imagen_url?: string;
}

export interface ReviewResult {
  is_compliant: boolean;
  violations: Array<{
    type: string;
    claim_found: string;
    location: string;
    severity: string;
  }>;
  approved_content: string | string[];
  disclaimers_added: string[];
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_flags: string[];
  modified: boolean;
  summary: string;
}

export interface CampaignCreatorState {
  // Step 1: Company Analysis
  companyUrl: string;
  setCompanyUrl: (url: string) => void;
  taxDna: TaxDNA | null;
  setTaxDna: (dna: TaxDNA) => void;
  isLoadingTaxDna: boolean;
  setIsLoadingTaxDna: (loading: boolean) => void;

  // Step 2: Campaign Objective
  campaignObjective: string;
  setCampaignObjective: (objective: string) => void;

  // Step 3: Campaign Selection
  campaignOptions: CampaignOption[];
  setCampaignOptions: (options: CampaignOption[]) => void;
  selectedOption: CampaignOption | null;
  selectOption: (option: CampaignOption) => void;

  // Step 4: Content Preview
  generatedContent: GeneratedPost[];
  setGeneratedContent: (content: GeneratedPost[]) => void;
  reviewResult: ReviewResult | null;
  setReviewResult: (result: ReviewResult) => void;

  // Navigation
  currentStep: number;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;

  // Publishing
  isPublishing: boolean;
  setIsPublishing: (publishing: boolean) => void;
  publishError: string | null;
  setPublishError: (error: string | null) => void;
  databaseCampaignId: string | null;
  setDatabaseCampaignId: (id: string | null) => void;

  // Utility
  resetWizard: () => void;
  isStepValid: (step: number) => boolean;
}

const initialState = {
  companyUrl: '',
  taxDna: null,
  isLoadingTaxDna: false,
  campaignObjective: '',
  campaignOptions: [],
  selectedOption: null,
  generatedContent: [],
  reviewResult: null,
  currentStep: 1,
  isPublishing: false,
  publishError: null,
  databaseCampaignId: null,
};

export const useCampaignCreator = create<CampaignCreatorState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setCompanyUrl: (url: string) => set({ companyUrl: url }),
      setTaxDna: (dna: TaxDNA) => set({ taxDna: dna }),
      setIsLoadingTaxDna: (loading: boolean) => set({ isLoadingTaxDna: loading }),

      setCampaignObjective: (objective: string) => set({ campaignObjective: objective }),

      setCampaignOptions: (options: CampaignOption[]) => set({ campaignOptions: options }),
      selectOption: (option: CampaignOption) => set({ selectedOption: option }),

      setGeneratedContent: (content: GeneratedPost[]) => set({ generatedContent: content }),
      setReviewResult: (result: ReviewResult) => set({ reviewResult: result }),

      nextStep: () => {
        const state = get();
        if (state.isStepValid(state.currentStep)) {
          set({ currentStep: Math.min(state.currentStep + 1, 4) });
        }
      },

      prevStep: () => {
        const state = get();
        set({ currentStep: Math.max(state.currentStep - 1, 1) });
      },

      goToStep: (step: number) => {
        if (step >= 1 && step <= 4) {
          set({ currentStep: step });
        }
      },

      setIsPublishing: (publishing: boolean) => set({ isPublishing: publishing }),
      setPublishError: (error: string | null) => set({ publishError: error }),
      setDatabaseCampaignId: (id: string | null) => set({ databaseCampaignId: id }),

      resetWizard: () => set(initialState),

      isStepValid: (step: number) => {
        const state = get();
        switch (step) {
          case 1:
            return !!state.companyUrl && state.companyUrl.length > 0;
          case 2:
            return !!state.campaignObjective && state.campaignObjective.length > 0;
          case 3:
            return !!state.selectedOption;
          case 4:
            return state.generatedContent.length > 0;
          default:
            return false;
        }
      },
    }),
    {
      name: 'campaign-creator-storage',
      partialize: (state) => ({
        companyUrl: state.companyUrl,
        taxDna: state.taxDna,
        campaignObjective: state.campaignObjective,
        campaignOptions: state.campaignOptions,
        selectedOption: state.selectedOption,
        generatedContent: state.generatedContent,
        reviewResult: state.reviewResult,
        currentStep: state.currentStep,
        databaseCampaignId: state.databaseCampaignId,
      }),
    }
  )
);
