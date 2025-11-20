import OpenAI from 'openai';
import { logger } from '../utils/logger';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface AgentAction {
  type: string;
  payload: any;
  reasoning: string;
  confidence: number;
}

export abstract class BaseAgent {
  protected name: string;
  protected systemPrompt: string;

  constructor(name: string, systemPrompt: string) {
    this.name = name;
    this.systemPrompt = systemPrompt;
  }

  abstract execute(action: string, data: any): Promise<any>;

  protected async chat(userPrompt: string): Promise<string> {
    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: this.systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      });

      return response.choices[0].message.content || '';
    } catch (error) {
      logger.error('OpenAI API error', { error, agent: this.name });
      throw error;
    }
  }

  protected async extractAction(userPrompt: string): Promise<AgentAction> {
    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: this.systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        tools: [
          {
            type: 'function',
            function: {
              name: 'execute_action',
              description: 'Execute an action based on user input',
              parameters: {
                type: 'object',
                properties: {
                  type: {
                    type: 'string',
                    description: 'The type of action to execute',
                  },
                  payload: {
                    type: 'object',
                    description: 'The data needed for the action',
                  },
                  reasoning: {
                    type: 'string',
                    description: 'Explanation of why this action was chosen',
                  },
                  confidence: {
                    type: 'number',
                    description: 'Confidence score between 0 and 1',
                  },
                },
                required: ['type', 'payload', 'reasoning', 'confidence'],
              },
            },
          },
        ],
        tool_choice: { type: 'function', function: { name: 'execute_action' } },
      });

      const toolCall = response.choices[0].message.tool_calls?.[0];
      if (!toolCall) {
        throw new Error('No tool call returned');
      }

      return JSON.parse(toolCall.function.arguments);
    } catch (error) {
      logger.error('Action extraction error', { error, agent: this.name });
      throw error;
    }
  }

  protected logAction(action: AgentAction) {
    logger.info('Agent action', {
      agent: this.name,
      action: action.type,
      confidence: action.confidence,
      reasoning: action.reasoning,
    });
  }
}
