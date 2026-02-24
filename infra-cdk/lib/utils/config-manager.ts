import * as fs from "fs"
import * as path from "path"
import * as yaml from "yaml"

const MAX_STACK_NAME_BASE_LENGTH = 35

export type DeploymentType = "docker" | "zip"

export interface AgentConfig {
  pattern: string
  name: string
}

export interface AppConfig {
  stack_name_base: string
  admin_user_email?: string | null
  backend: {
    pattern?: string  // Legacy single agent mode
    agents?: AgentConfig[]  // New multi-agent mode
    deployment_type: DeploymentType
  }
}

export class ConfigManager {
  private config: AppConfig

  constructor(configFile: string) {
    this.config = this._loadConfig(configFile)
  }

  private _loadConfig(configFile: string): AppConfig {
    const configPath = path.join(__dirname, "..", "..", configFile)

    if (!fs.existsSync(configPath)) {
      throw new Error(`Configuration file ${configPath} does not exist. Please create config.yaml file.`)
    }

    try {
      const fileContent = fs.readFileSync(configPath, "utf8")
      const parsedConfig = yaml.parse(fileContent) as AppConfig

      const deploymentType = parsedConfig.backend?.deployment_type || "docker"
      if (deploymentType !== "docker" && deploymentType !== "zip") {
        throw new Error(`Invalid deployment_type '${deploymentType}'. Must be 'docker' or 'zip'.`)
      }

      const stackNameBase = parsedConfig.stack_name_base
      if (!stackNameBase) {
        throw new Error("stack_name_base is required in config.yaml")
      }
      if (stackNameBase.length > MAX_STACK_NAME_BASE_LENGTH) {
        throw new Error(
          `stack_name_base '${stackNameBase}' is too long (${stackNameBase.length} chars). ` +
            `Maximum length is ${MAX_STACK_NAME_BASE_LENGTH} characters due to AWS AgentCore runtime naming constraints.`
        )
      }

      // Support both legacy single agent and new multi-agent modes
      const backend = parsedConfig.backend
      if (!backend) {
        throw new Error("backend configuration is required in config.yaml")
      }

      // Validate that either pattern or agents is provided
      if (!backend.pattern && (!backend.agents || backend.agents.length === 0)) {
        throw new Error("backend must have either 'pattern' (single agent) or 'agents' array (multi-agent)")
      }

      // If both are provided, prefer agents array
      if (backend.pattern && backend.agents && backend.agents.length > 0) {
        console.warn("Both 'pattern' and 'agents' provided in config. Using 'agents' array.")
      }

      return {
        stack_name_base: stackNameBase,
        admin_user_email: parsedConfig.admin_user_email || null,
        backend: {
          pattern: backend.pattern,
          agents: backend.agents,
          deployment_type: deploymentType,
        },
      }
    } catch (error) {
      throw new Error(`Failed to parse configuration file ${configPath}: ${error}`)
    }
  }

  public getProps(): AppConfig {
    return this.config
  }

  public get(key: string, defaultValue?: any): any {
    const keys = key.split(".")
    let value: any = this.config

    for (const k of keys) {
      if (typeof value === "object" && value !== null && k in value) {
        value = value[k]
      } else {
        return defaultValue
      }
    }

    return value
  }
}
