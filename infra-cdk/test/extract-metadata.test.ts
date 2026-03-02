import * as fs from 'fs'
import * as path from 'path'

/**
 * Test the metadata extraction logic that will be used in BackendStack.
 * This validates the regex patterns work correctly with real agent files.
 */
describe('Agent Metadata Extraction', () => {
  /**
   * Extract agent metadata (tools, model ID, and system prompt) from agent Python source code.
   * This is a copy of the BackendStack method for testing purposes.
   */
  function extractAgentMetadata(agentFilePath: string): {
    tools: string[]
    modelId: string
    systemPrompt: string
  } {
    try {
      const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')
      
      // Extract tools list from the agent file
      const toolsMatch = sourceCode.match(/tools\s*=\s*\[([\s\S]*?)\]/m)
      let tools: string[] = []
      
      if (toolsMatch) {
        tools = toolsMatch[1]
          .split(',')
          .map(t => t.trim().replace(/['"]/g, ''))
          .filter(t => t && !t.startsWith('#'))
          .map(t => t.includes('.') ? t.split('.').pop() || t : t)
          .filter(Boolean)
      }
      
      // Extract model ID from the agent file
      const modelMatch = sourceCode.match(/model_id\s*=\s*["']([^"']+)["']/)
      const modelId = modelMatch ? modelMatch[1] : 'unknown'
      
      // Extract system prompt from the agent file
      // Matches patterns like: system_prompt = """...""" or system_prompt = '''...'''
      // Handles multi-line strings with triple quotes
      let systemPrompt = ''
      
      // Try to match triple-quoted strings (both """ and ''')
      const systemPromptMatch = sourceCode.match(
        /system_prompt\s*=\s*(?:"""([\s\S]*?)"""|'''([\s\S]*?)''')/
      )
      
      if (systemPromptMatch) {
        // Use whichever capture group matched (group 1 for """, group 2 for ''')
        systemPrompt = (systemPromptMatch[1] || systemPromptMatch[2] || '').trim()
      } else {
        // Try to match SYSTEM_PROMPT constant (uppercase variant)
        const constantMatch = sourceCode.match(
          /SYSTEM_PROMPT\s*=\s*(?:"""([\s\S]*?)"""|'''([\s\S]*?)''')/
        )
        if (constantMatch) {
          systemPrompt = (constantMatch[1] || constantMatch[2] || '').trim()
        }
      }
      
      return { tools, modelId, systemPrompt }
    } catch (error) {
      console.warn(`Failed to extract metadata from ${agentFilePath}:`, error)
      return { tools: [], modelId: 'unknown', systemPrompt: '' }
    }
  }

  test('extracts tools and model from basic_agent.py', () => {
    const agentPath = path.resolve(__dirname, '../../patterns/strands-single-agent/basic_agent.py')
    const metadata = extractAgentMetadata(agentPath)
    
    expect(metadata.tools).toContain('gateway_client')
    expect(metadata.tools).toContain('execute_python_securely')
    expect(metadata.modelId).toBe('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    expect(metadata.systemPrompt).toBeTruthy()
    expect(metadata.systemPrompt).toContain('helpful assistant')
  })

  test('extracts tools and model from colorado_agent.py', () => {
    const agentPath = path.resolve(__dirname, '../../patterns/strands-colorado-agent/colorado_agent.py')
    const metadata = extractAgentMetadata(agentPath)
    
    // Colorado agent has empty tools list
    expect(metadata.tools).toEqual([])
    expect(metadata.modelId).toBe('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    expect(metadata.systemPrompt).toBeTruthy()
    expect(metadata.systemPrompt).toContain('Denver')
  })

  test('extracts tools and model from umich_agent.py', () => {
    const agentPath = path.resolve(__dirname, '../../patterns/strands-umich-agent/umich_agent.py')
    const metadata = extractAgentMetadata(agentPath)
    
    expect(metadata.tools).toContain('http_request')
    expect(metadata.tools).toContain('current_time')
    expect(metadata.modelId).toBe('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    expect(metadata.systemPrompt).toBeTruthy()
    expect(metadata.systemPrompt).toContain('University of Michigan')
  })

  test('extracts tools and model from coder_agent.py', () => {
    const agentPath = path.resolve(__dirname, '../../patterns/strands-coder-agent/coder_agent.py')
    const metadata = extractAgentMetadata(agentPath)
    
    expect(metadata.tools).toContain('execute_python')
    expect(metadata.modelId).toBe('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    expect(metadata.systemPrompt).toBeTruthy()
    expect(metadata.systemPrompt).toContain('code execution')
  })

  test('handles missing file gracefully', () => {
    const agentPath = '/nonexistent/path/agent.py'
    const metadata = extractAgentMetadata(agentPath)
    
    expect(metadata.tools).toEqual([])
    expect(metadata.modelId).toBe('unknown')
    expect(metadata.systemPrompt).toBe('')
  })

  test('handles malformed source code gracefully', () => {
    // Create a temporary file with malformed content
    const tempPath = path.resolve(__dirname, 'temp-malformed.py')
    fs.writeFileSync(tempPath, 'this is not valid python code')
    
    const metadata = extractAgentMetadata(tempPath)
    
    expect(metadata.tools).toEqual([])
    expect(metadata.modelId).toBe('unknown')
    expect(metadata.systemPrompt).toBe('')
    
    // Clean up
    fs.unlinkSync(tempPath)
  })
})
