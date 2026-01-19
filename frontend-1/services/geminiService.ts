import { GoogleGenAI, Type } from "@google/genai";

// Initialize Gemini Client
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || 'mock-key' });

export interface SmartSearchCriteria {
  subject?: string;
  maxPrice?: number;
  keywords?: string[];
  minRating?: number;
}

/**
 * Uses Gemini to parse a natural language query into structured filter criteria.
 * Example: "I need a cheap math tutor for calculus" -> { subject: "Mathematics", maxPrice: 50, keywords: ["Calculus"] }
 */
export const parseSearchQuery = async (query: string): Promise<SmartSearchCriteria> => {
  if (!process.env.API_KEY) {
    console.warn("API Key missing, returning default search.");
    return { keywords: [query] };
  }

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Extract search criteria from this student query: "${query}". 
      Available subjects are: Mathematics, Physics, Computer Science, English Literature, Chemistry, History.
      If a specific price is mentioned (e.g. under $50), set maxPrice.
      If quality words are used (e.g. expert, best), set minRating to 4.8.
      `,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            subject: { type: Type.STRING, description: "The normalized subject name" },
            maxPrice: { type: Type.NUMBER, description: "Maximum hourly rate inferred" },
            minRating: { type: Type.NUMBER, description: "Minimum rating inferred" },
            keywords: { 
              type: Type.ARRAY, 
              items: { type: Type.STRING }, 
              description: "Specific topics or skills mentioned" 
            }
          }
        }
      }
    });

    if (response.text) {
      return JSON.parse(response.text) as SmartSearchCriteria;
    }
    return {};
  } catch (error) {
    console.error("Gemini search parsing failed", error);
    return { keywords: [query] };
  }
};