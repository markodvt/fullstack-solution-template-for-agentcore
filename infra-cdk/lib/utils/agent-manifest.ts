import * as path from "path"
import * as fs from "fs"

/**
 * Interface for agent metadata from agents.json manifest.
 * Defines the structure of each agent entry in the manifest.
 */
export interface AgentManifestEntry {
  /** Unique identifier for the agent (e.g., "orchestrator", "colorado") */
  name: string
  /** Human-readable display name for the agent (e.g., "Orchestrator") */
  displayName: string
  /** Description of the agent's purpose and capabilities */
  description: string
  /** Runtime identifier used for AgentCore Runtime naming */
  runtimeId: string
  /** Whether this agent is the default agent for the pattern */
  isDefault: boolean
}

/**
 * Interface for the complete agents.json structure.
 * The manifest file must contain an array of agent entries.
 */
export interface AgentManifest {
  /** Array of agent definitions */
  agents: AgentManifestEntry[]
}

/**
 * Validates an agent manifest entry has all required fields with proper types.
 * Throws descriptive errors if validation fails.
 * 
 * @param entry - Agent manifest entry to validate
 * @param index - Index in agents array (for error messages)
 * @throws Error if validation fails with specific field information
 */
export function validateAgentEntry(entry: any, index: number): void {
  const requiredFields = ["name", "displayName", "description", "runtimeId", "isDefault"]

  for (const field of requiredFields) {
    if (!(field in entry)) {
      throw new Error(`Agent entry at index ${index} is missing required field: ${field}`)
    }

    if (field !== "isDefault" && (!entry[field] || entry[field].trim() === "")) {
      throw new Error(
        `Agent entry at index ${index} has empty value for required field: ${field}`
      )
    }
  }

  if (typeof entry.isDefault !== "boolean") {
    throw new Error(
      `Agent entry at index ${index} has invalid isDefault value (must be boolean)`
    )
  }
}

/**
 * Loads and validates agents.json manifest from pattern directory.
 * Performs comprehensive validation including:
 * - File existence and JSON parsing
 * - Required fields presence and types
 * - Exactly one default agent
 * - Non-empty agents array
 * 
 * @param patternPath - Absolute path to pattern directory
 * @returns Validated agent manifest with all agent entries
 * @throws Error if manifest is missing, malformed, or invalid with descriptive message
 */
export function loadAgentManifest(patternPath: string): AgentManifest {
  const manifestPath = path.join(patternPath, "agents.json")

  if (!fs.existsSync(manifestPath)) {
    throw new Error(
      `Agent manifest not found at ${manifestPath}. ` +
        `Multi-agent patterns must include agents.json manifest.`
    )
  }

  let manifest: AgentManifest
  try {
    const content = fs.readFileSync(manifestPath, "utf-8")
    manifest = JSON.parse(content)
  } catch (error) {
    throw new Error(`Failed to parse agents.json manifest at ${manifestPath}: ${error}`)
  }

  if (!manifest.agents || !Array.isArray(manifest.agents)) {
    throw new Error(`Invalid agents.json: must contain "agents" array`)
  }

  if (manifest.agents.length === 0) {
    throw new Error(`Invalid agents.json: "agents" array cannot be empty`)
  }

  // Validate each agent entry
  manifest.agents.forEach((entry, index) => {
    validateAgentEntry(entry, index)
  })

  // Validate exactly one default agent
  const defaultAgents = manifest.agents.filter((a) => a.isDefault)
  if (defaultAgents.length === 0) {
    throw new Error(`Invalid agents.json: must have exactly one agent with isDefault: true`)
  }
  if (defaultAgents.length > 1) {
    throw new Error(
      `Invalid agents.json: multiple agents marked as default (${defaultAgents.map((a) => a.name).join(", ")})`
    )
  }

  return manifest
}
