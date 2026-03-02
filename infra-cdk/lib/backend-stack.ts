import * as cdk from "aws-cdk-lib"
import * as cognito from "aws-cdk-lib/aws-cognito"
import * as iam from "aws-cdk-lib/aws-iam"
import * as ssm from "aws-cdk-lib/aws-ssm"
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager"
import * as dynamodb from "aws-cdk-lib/aws-dynamodb"
import * as apigateway from "aws-cdk-lib/aws-apigateway"
import * as logs from "aws-cdk-lib/aws-logs"
import * as s3 from "aws-cdk-lib/aws-s3"
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment"
import * as agentcore from "@aws-cdk/aws-bedrock-agentcore-alpha"
import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore"
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha"
import * as lambda from "aws-cdk-lib/aws-lambda"
import * as ecr_assets from "aws-cdk-lib/aws-ecr-assets"
import * as cr from "aws-cdk-lib/custom-resources"
import { Construct } from "constructs"
import { AppConfig } from "./utils/config-manager"
import { AgentCoreRole } from "./utils/agentcore-role"
import { loadAgentManifest, AgentManifestEntry } from "./utils/agent-manifest"
import * as path from "path"
import * as fs from "fs"

export interface BackendStackProps extends cdk.NestedStackProps {
  config: AppConfig
  userPoolId: string
  userPoolClientId: string
  userPoolDomain: cognito.UserPoolDomain
  frontendUrl: string
}

export class BackendStack extends cdk.NestedStack {
  public readonly userPoolId: string
  public readonly userPoolClientId: string
  public readonly userPoolDomain: cognito.UserPoolDomain
  public feedbackApiUrl: string
  public runtimeArn: string
  public memoryArn: string
  private agentName: cdk.CfnParameter
  private networkMode: cdk.CfnParameter
  private userPool: cognito.IUserPool
  private machineClient: cognito.UserPoolClient
  private agentRuntime: agentcore.Runtime
  private api: apigateway.RestApi

  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props)

    // Store the Cognito values
    this.userPoolId = props.userPoolId
    this.userPoolClientId = props.userPoolClientId
    this.userPoolDomain = props.userPoolDomain

    // Import the Cognito resources from the other stack
    this.userPool = cognito.UserPool.fromUserPoolId(
      this,
      "ImportedUserPoolForBackend",
      props.userPoolId
    )
    // then create the user pool client
    cognito.UserPoolClient.fromUserPoolClientId(
      this,
      "ImportedUserPoolClient",
      props.userPoolClientId
    )

    // Create Machine-to-Machine authentication components
    this.createMachineAuthentication(props.config)

    // DEPLOYMENT ORDER EXPLANATION:
    // 1. Cognito User Pool & Client (created in separate CognitoStack)
    // 2. Machine Client & Resource Server (created above for M2M auth)
    // 3. AgentCore Gateway (created next - uses machine client for auth)
    // 4. AgentCore Runtime (created last - independent of gateway)
    //
    // This order ensures that authentication components are available before
    // the gateway that depends on them, while keeping the runtime separate
    // since it doesn't directly depend on the gateway.

    // Create AgentCore Gateway (before Runtime)
    this.createAgentCoreGateway(props.config)

    // Create AgentCore Runtime resources
    this.createAgentCoreRuntime(props.config)

    // Store runtime ARN in SSM for frontend stack
    this.createRuntimeSSMParameters(props.config)

    // Store Cognito configuration in SSM for testing and frontend
    this.createCognitoSSMParameters(props.config)

    // Create Feedback DynamoDB table (example of application data storage)
    const feedbackTable = this.createFeedbackTable(props.config)

    // Create API Gateway Feedback API resources (example of best-practice API Gateway + Lambda
    // pattern)
    this.createFeedbackApi(props.config, props.frontendUrl, feedbackTable)

    // Create Agent Discovery API endpoint on the existing API Gateway
    this.createAgentDiscoveryApi(props.config, props.frontendUrl)
  }

  /**
   * Creates AgentCore Runtime(s) based on pattern type.
   * Detects multi-agent patterns by checking for agents.json manifest.
   * Routes to appropriate deployment method based on pattern type.
   * 
   * @param config - Application configuration
   */
  private createAgentCoreRuntime(config: AppConfig): void {
    const pattern = config.backend?.pattern || "strands-single-agent"

    // Detect if this is a multi-agent pattern by checking for agents.json
    const patternPath = path.resolve(__dirname, "..", "..", "patterns", pattern)
    const manifestPath = path.join(patternPath, "agents.json")
    const isMultiAgentPattern = fs.existsSync(manifestPath)

    if (isMultiAgentPattern) {
      // Multi-agent deployment: read manifest and create multiple runtimes
      this.createMultiAgentRuntimes(config, pattern, patternPath)
    } else {
      // Single-agent deployment: existing logic
      this.createSingleAgentRuntime(config, pattern, patternPath)
    }
  }

  /**
   * Creates a single AgentCore Runtime for traditional single-agent patterns.
   * This method contains the original runtime creation logic for backward compatibility.
   * 
   * @param config - Application configuration
   * @param pattern - Pattern name (e.g., "strands-single-agent")
   * @param patternPath - Absolute path to pattern directory
   */
  private createSingleAgentRuntime(
    config: AppConfig,
    pattern: string,
    patternPath: string
  ): void {
    // Parameters
    this.agentName = new cdk.CfnParameter(this, "AgentName", {
      type: "String",
      default: "StrandsAgent",
      description: "Name for the agent runtime",
    })

    this.networkMode = new cdk.CfnParameter(this, "NetworkMode", {
      type: "String",
      default: "PUBLIC",
      description: "Network mode for AgentCore resources",
      allowedValues: ["PUBLIC", "PRIVATE"],
    })

    const stack = cdk.Stack.of(this)
    const deploymentType = config.backend.deployment_type

    // Create the agent runtime artifact based on deployment type
    let agentRuntimeArtifact: agentcore.AgentRuntimeArtifact
    let zipPackagerResource: cdk.CustomResource | undefined

    if (deploymentType === "zip") {
      // ZIP DEPLOYMENT: Use Lambda to package and upload to S3 (no Docker required)
      const repoRoot = path.resolve(__dirname, "..", "..")
      const patternDir = path.join(repoRoot, "patterns", pattern)

      // Create S3 bucket for agent code
      const agentCodeBucket = new s3.Bucket(this, "AgentCodeBucket", {
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
        versioned: true,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      })

      // Lambda to package agent code
      const packagerLambda = new lambda.Function(this, "ZipPackagerLambda", {
        runtime: lambda.Runtime.PYTHON_3_12,
        handler: "index.handler",
        code: lambda.Code.fromAsset(path.join(__dirname, "..", "lambdas", "zip-packager")),
        timeout: cdk.Duration.minutes(10),
        memorySize: 1024,
        ephemeralStorageSize: cdk.Size.gibibytes(2),
      })

      agentCodeBucket.grantReadWrite(packagerLambda)

      // Read agent code files and encode as base64
      const agentCode: Record<string, string> = {}
      
      // Read pattern .py files
      for (const file of fs.readdirSync(patternDir)) {
        if (file.endsWith(".py")) {
          const content = fs.readFileSync(path.join(patternDir, file))
          agentCode[file] = content.toString("base64")
        }
      }

      // Read shared modules (gateway/, tools/)
      for (const module of ["gateway", "tools"]) {
        const moduleDir = path.join(repoRoot, module)
        if (fs.existsSync(moduleDir)) {
          this.readDirRecursive(moduleDir, module, agentCode)
        }
      }

      // Read requirements
      const requirementsPath = path.join(patternDir, "requirements.txt")
      const requirements = fs.readFileSync(requirementsPath, "utf-8")
        .split("\n")
        .map(line => line.trim())
        .filter(line => line && !line.startsWith("#"))

      // Create hash for change detection
      // We use this to trigger update when content changes
      const contentHash = this.hashContent(JSON.stringify({ requirements, agentCode }))

      // Custom Resource to trigger packaging
      const provider = new cr.Provider(this, "ZipPackagerProvider", {
        onEventHandler: packagerLambda,
      })

      zipPackagerResource = new cdk.CustomResource(this, "ZipPackager", {
        serviceToken: provider.serviceToken,
        properties: {
          BucketName: agentCodeBucket.bucketName,
          ObjectKey: "deployment_package.zip",
          Requirements: requirements,
          AgentCode: agentCode,
          ContentHash: contentHash,
        },
      })

      // Store bucket name in SSM for updates
      new ssm.StringParameter(this, "AgentCodeBucketNameParam", {
        parameterName: `/${config.stack_name_base}/agent-code-bucket`,
        stringValue: agentCodeBucket.bucketName,
        description: "S3 bucket for agent code deployment packages",
      })

      agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromS3(
        {
          bucketName: agentCodeBucket.bucketName,
          objectKey: "deployment_package.zip",
        },
        agentcore.AgentCoreRuntime.PYTHON_3_12,
        ["opentelemetry-instrument", "basic_agent.py"]
      )
    } else {
      // DOCKER DEPLOYMENT: Use container-based deployment
      agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
        path.resolve(__dirname, "..", ".."),
        {
          platform: ecr_assets.Platform.LINUX_ARM64,
          file: `patterns/${pattern}/Dockerfile`,
        }
      )
    }

    // Configure network mode
    const networkConfiguration =
      this.networkMode.valueAsString === "PRIVATE"
        ? undefined // For private mode, you would need to configure VPC settings
        : agentcore.RuntimeNetworkConfiguration.usingPublicNetwork()

    // Configure JWT authorizer with Cognito
    const authorizerConfiguration = agentcore.RuntimeAuthorizerConfiguration.usingJWT(
      `https://cognito-idp.${stack.region}.amazonaws.com/${this.userPoolId}/.well-known/openid-configuration`,
      [this.userPoolClientId]
    )

    // Create AgentCore execution role
    const agentRole = new AgentCoreRole(this, "AgentCoreRole")

    // Create memory resource with long-term memory strategies enabled
    // For more details, see docs/MEMORY_INTEGRATION.md
    const memory = new cdk.CfnResource(this, "AgentMemory", {
      type: "AWS::BedrockAgentCore::Memory",
      properties: {
        Name: cdk.Names.uniqueResourceName(this, { maxLength: 48 }),
        EventExpiryDuration: 30,
        Description: `Memory with long-term strategies for ${config.stack_name_base} agent`,
        MemoryStrategies: [
          {
            SummaryMemoryStrategy: {
              Name: "SessionSummarizer",
              Namespaces: ["/summaries/{actorId}/{sessionId}"],
            },
          },
          {
            UserPreferenceMemoryStrategy: {
              Name: "PreferenceLearner",
              Namespaces: ["/preferences/{actorId}"],
            },
          },
          {
            SemanticMemoryStrategy: {
              Name: "FactExtractor",
              Namespaces: ["/facts/{actorId}"],
            },
          },
        ],
        MemoryExecutionRoleArn: agentRole.roleArn,
        Tags: {
          Name: `${config.stack_name_base}_Memory`,
          ManagedBy: "CDK",
        },
      },
    })
    const memoryId = memory.getAtt("MemoryId").toString()
    const memoryArn = memory.getAtt("MemoryArn").toString()

    // Store the memory ARN for access from main stack
    this.memoryArn = memoryArn

    // Add memory-specific permissions to agent role
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "MemoryResourceAccess",
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:ListEvents",
          "bedrock-agentcore:RetrieveMemoryRecords", // Only needed for long-term strategies
        ],
        resources: [memoryArn],
      })
    )

    // Add SSM permissions for Gateway URL lookup
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "SSMParameterAccess",
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/${config.stack_name_base}/*`,
        ],
      })
    )

    // Add Code Interpreter permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "CodeInterpreterAccess",
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock-agentcore:StartCodeInterpreterSession",
          "bedrock-agentcore:StopCodeInterpreterSession",
          "bedrock-agentcore:InvokeCodeInterpreter",
        ],
        resources: [`arn:aws:bedrock-agentcore:${this.region}:aws:code-interpreter/*`],
      })
    )

    // Environment variables for the runtime
    const envVars: { [key: string]: string } = {
      AWS_REGION: stack.region,
      AWS_DEFAULT_REGION: stack.region,
      MEMORY_ID: memoryId,
      STACK_NAME: config.stack_name_base, // Required for agent to find SSM parameters
    }

    // Create the runtime using L2 construct
    // requestHeaderConfiguration allows the agent to read the Authorization header
    // from RequestContext.request_headers, which is needed to securely extract the
    // user ID from the validated JWT token (sub claim) instead of trusting the payload body.
    this.agentRuntime = new agentcore.Runtime(this, "Runtime", {
      runtimeName: `${config.stack_name_base.replace(/-/g, "_")}_${this.agentName.valueAsString}`,
      agentRuntimeArtifact: agentRuntimeArtifact,
      executionRole: agentRole,
      networkConfiguration: networkConfiguration,
      protocolConfiguration: agentcore.ProtocolType.HTTP,
      environmentVariables: envVars,
      authorizerConfiguration: authorizerConfiguration,
      requestHeaderConfiguration: {
        allowlistedHeaders: ["Authorization"],
      },
      description: `${pattern} agent runtime for ${config.stack_name_base}`,
    })

    // Make sure that ZIP is uploaded before Runtime is created
    if (zipPackagerResource) {
      this.agentRuntime.node.addDependency(zipPackagerResource)
    }

    // Store the runtime ARN
    this.runtimeArn = this.agentRuntime.agentRuntimeArn

    // Outputs
    new cdk.CfnOutput(this, "AgentRuntimeId", {
      description: "ID of the created agent runtime",
      value: this.agentRuntime.agentRuntimeId,
    })

    new cdk.CfnOutput(this, "AgentRuntimeArn", {
      description: "ARN of the created agent runtime",
      value: this.agentRuntime.agentRuntimeArn,
      exportName: `${config.stack_name_base}-AgentRuntimeArn`,
    })

    new cdk.CfnOutput(this, "AgentRoleArn", {
      description: "ARN of the agent execution role",
      value: agentRole.roleArn,
    })

    // Memory ARN output
    new cdk.CfnOutput(this, "MemoryArn", {
      description: "ARN of the agent memory resource",
      value: memoryArn,
    })
  }

  private createRuntimeSSMParameters(config: AppConfig): void {
    // Store runtime ARN in SSM for frontend stack
    new ssm.StringParameter(this, "RuntimeArnParam", {
      parameterName: `/${config.stack_name_base}/runtime-arn`,
      stringValue: this.runtimeArn,
    })
  }

  private createCognitoSSMParameters(config: AppConfig): void {
    // Store Cognito configuration in SSM for testing and frontend access
    new ssm.StringParameter(this, "CognitoUserPoolIdParam", {
      parameterName: `/${config.stack_name_base}/cognito-user-pool-id`,
      stringValue: this.userPoolId,
      description: "Cognito User Pool ID",
    })

    new ssm.StringParameter(this, "CognitoUserPoolClientIdParam", {
      parameterName: `/${config.stack_name_base}/cognito-user-pool-client-id`,
      stringValue: this.userPoolClientId,
      description: "Cognito User Pool Client ID",
    })

    new ssm.StringParameter(this, "MachineClientIdParam", {
      parameterName: `/${config.stack_name_base}/machine_client_id`,
      stringValue: this.machineClient.userPoolClientId,
      description: "Machine Client ID for M2M authentication",
    })

    new secretsmanager.Secret(this, "MachineClientSecret", {
      secretName: `/${config.stack_name_base}/machine_client_secret`,
      secretStringValue: cdk.SecretValue.unsafePlainText(this.machineClient.userPoolClientSecret.unsafeUnwrap()),
      description: "Machine Client Secret for M2M authentication",
    })

    // Use the correct Cognito domain format from the passed domain
    new ssm.StringParameter(this, "CognitoDomainParam", {
      parameterName: `/${config.stack_name_base}/cognito_provider`,
      stringValue: `${this.userPoolDomain.domainName}.auth.${cdk.Aws.REGION}.amazoncognito.com`,
      description: "Cognito domain URL for token endpoint",
    })
  }

  // Creates a DynamoDB table for storing user feedback.
  private createFeedbackTable(config: AppConfig): dynamodb.Table {
    const feedbackTable = new dynamodb.Table(this, "FeedbackTable", {
      tableName: `${config.stack_name_base}-feedback`,
      partitionKey: {
        name: "feedbackId",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    })

    // Add GSI for querying by feedbackType with timestamp sorting
    feedbackTable.addGlobalSecondaryIndex({
      indexName: "feedbackType-timestamp-index",
      partitionKey: {
        name: "feedbackType",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "timestamp",
        type: dynamodb.AttributeType.NUMBER,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    })

    return feedbackTable
  }

  /**
   * Creates an API Gateway with Lambda integration for the feedback endpoint.
   * This is an EXAMPLE implementation demonstrating best practices for API Gateway + Lambda.
   *
   * API Contract - POST /feedback
   * Authorization: Bearer <cognito-access-token> (required)
   *
   * Request Body:
   *   sessionId: string (required, max 100 chars, alphanumeric with -_) - Conversation session ID
   *   message: string (required, max 5000 chars) - Agent's response being rated
   *   feedbackType: "positive" | "negative" (required) - User's rating
   *   comment: string (optional, max 5000 chars) - User's explanation for rating
   *
   * Success Response (200):
   *   { success: true, feedbackId: string }
   *
   * Error Responses:
   *   400: { error: string } - Validation failure (missing fields, invalid format)
   *   401: { error: "Unauthorized" } - Invalid/missing JWT token
   *   500: { error: "Internal server error" } - DynamoDB or processing error
   *
   * Implementation: infra-cdk/lambdas/feedback/index.py
   */
  private createFeedbackApi(
    config: AppConfig,
    frontendUrl: string,
    feedbackTable: dynamodb.Table
  ): void {
    // Create Lambda function for feedback using Python
    const feedbackLambda = new PythonFunction(this, "FeedbackLambda", {
      functionName: `${config.stack_name_base}-feedback`,
      runtime: lambda.Runtime.PYTHON_3_13,
      entry: path.join(__dirname, "..", "lambdas", "feedback"),
      handler: "handler",
      environment: {
        TABLE_NAME: feedbackTable.tableName,
        CORS_ALLOWED_ORIGINS: `${frontendUrl},http://localhost:3000`,
      },
      timeout: cdk.Duration.seconds(30),
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          "PowertoolsLayer",
          `arn:aws:lambda:${
            cdk.Stack.of(this).region
          }:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-arm64:18`
        ),
      ],
      logGroup: new logs.LogGroup(this, "FeedbackLambdaLogGroup", {
        logGroupName: `/aws/lambda/${config.stack_name_base}-feedback`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    })

    // Grant Lambda permissions to write to DynamoDB
    feedbackTable.grantWriteData(feedbackLambda)

    /*
     * CORS TODO: Wildcard (*) used because Backend deploys before Frontend in nested stack order.
     * For Lambda proxy integrations, the Lambda's ALLOWED_ORIGINS env var is the primary CORS control.
     * API Gateway defaultCorsPreflightOptions below only handles OPTIONS preflight requests.
     * See detailed explanation and fix options in: infra-cdk/lambdas/feedback/index.py
     */
    this.api = new apigateway.RestApi(this, "FeedbackApi", {
      restApiName: `${config.stack_name_base}-api`,
      description: "API for user feedback and future endpoints",
      defaultCorsPreflightOptions: {
        allowOrigins: [frontendUrl, "http://localhost:3000"],
        allowMethods: ["POST", "GET", "OPTIONS"],
        allowHeaders: ["Content-Type", "Authorization"],
      },
      deployOptions: {
        stageName: "prod",
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
        cachingEnabled: true,
        cacheClusterEnabled: true,
        cacheClusterSize: "0.5",
        cacheTtl: cdk.Duration.minutes(5),
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        accessLogDestination: new apigateway.LogGroupLogDestination(
          new logs.LogGroup(this, "FeedbackApiAccessLogGroup", {
            logGroupName: `/aws/apigateway/${config.stack_name_base}-api-access`,
            retention: logs.RetentionDays.ONE_WEEK,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
          })
        ),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields(),
        tracingEnabled: true,
      },
    })

    // Add request validator for API security
    const requestValidator = new apigateway.RequestValidator(this, "FeedbackApiRequestValidator", {
      restApi: this.api,
      requestValidatorName: `${config.stack_name_base}-request-validator`,
      validateRequestBody: true,
      validateRequestParameters: true,
    })

    // Create Cognito authorizer
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, "FeedbackApiAuthorizer", {
      cognitoUserPools: [this.userPool],
      identitySource: "method.request.header.Authorization",
      authorizerName: `${config.stack_name_base}-authorizer`,
    })

    // Create /feedback resource and POST method
    const feedbackResource = this.api.root.addResource("feedback")
    feedbackResource.addMethod("POST", new apigateway.LambdaIntegration(feedbackLambda), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
      requestValidator: requestValidator,
    })

    // Store the API URL for access from main stack
    this.feedbackApiUrl = this.api.url

    // Store API URL in SSM for frontend
    new ssm.StringParameter(this, "FeedbackApiUrlParam", {
      parameterName: `/${config.stack_name_base}/feedback-api-url`,
      stringValue: this.api.url,
      description: "Feedback API Gateway URL",
    })
  }

  /**
   * Creates the Agent Discovery API endpoint on the existing API Gateway.
   * This endpoint allows the frontend to discover available agents by querying
   * SSM Parameter Store for agent metadata.
   * 
   * @param config - Application configuration containing stack name
   * @param frontendUrl - Frontend URL for CORS configuration
   * 
   * Implementation: infra-cdk/lambdas/agent-discovery/index.py
   */
  private createAgentDiscoveryApi(
    config: AppConfig,
    frontendUrl: string
  ): void {
    // Create Lambda function for agent discovery using Python
    const agentDiscoveryLambda = new PythonFunction(this, "AgentDiscoveryLambda", {
      functionName: `${config.stack_name_base}-agent-discovery`,
      runtime: lambda.Runtime.PYTHON_3_13,
      entry: path.join(__dirname, "..", "lambdas", "agent-discovery"),
      handler: "handler",
      environment: {
        STACK_NAME_BASE: config.stack_name_base,
        CORS_ALLOWED_ORIGINS: `${frontendUrl},http://localhost:3000`,
      },
      timeout: cdk.Duration.seconds(30),
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          "AgentDiscoveryPowertoolsLayer",
          `arn:aws:lambda:${
            cdk.Stack.of(this).region
          }:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-arm64:18`
        ),
      ],
      logGroup: new logs.LogGroup(this, "AgentDiscoveryLambdaLogGroup", {
        logGroupName: `/aws/lambda/${config.stack_name_base}-agent-discovery`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    })

    // Grant Lambda permissions to read SSM parameters for agent metadata
    agentDiscoveryLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
        ],
        resources: [
          // Allow access to the agents path itself
          `arn:aws:ssm:${cdk.Stack.of(this).region}:${
            cdk.Stack.of(this).account
          }:parameter/${config.stack_name_base}/agents`,
          // Allow access to all parameters under the agents path
          `arn:aws:ssm:${cdk.Stack.of(this).region}:${
            cdk.Stack.of(this).account
          }:parameter/${config.stack_name_base}/agents/*`,
        ],
      })
    )

    // Grant Lambda permissions to read agent source code from S3
    agentDiscoveryLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:GetObject", "s3:ListBucket"],
        resources: [
          `arn:aws:s3:::${config.stack_name_base}-agent-source-code`,
          `arn:aws:s3:::${config.stack_name_base}-agent-source-code/*`,
        ],
      })
    )

    // Create Cognito authorizer (reuse from feedback API)
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(
      this,
      "AgentDiscoveryApiAuthorizer",
      {
        cognitoUserPools: [this.userPool],
        identitySource: "method.request.header.Authorization",
        authorizerName: `${config.stack_name_base}-agent-discovery-authorizer`,
      }
    )

    // Add /agents resource and GET method to existing API
    const agentsResource = this.api.root.addResource("agents")
    agentsResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(agentDiscoveryLambda),
      {
        authorizer,
        authorizationType: apigateway.AuthorizationType.COGNITO,
      }
    )

    // Store agent discovery API URL in SSM for frontend
    new ssm.StringParameter(this, "AgentDiscoveryApiUrlParam", {
      parameterName: `/${config.stack_name_base}/agent-discovery-api-url`,
      stringValue: `${this.api.url}agents`,
      description: "Agent Discovery API endpoint URL",
    })
  }

  private createAgentCoreGateway(config: AppConfig): void {
    // Create sample tool Lambda
    const toolLambda = new lambda.Function(this, "SampleToolLambda", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "sample_tool_lambda.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../gateway/tools/sample_tool")),
      timeout: cdk.Duration.seconds(30),
      logGroup: new logs.LogGroup(this, "SampleToolLambdaLogGroup", {
        logGroupName: `/aws/lambda/${config.stack_name_base}-sample-tool`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    })

    // Create comprehensive IAM role for gateway
    const gatewayRole = new iam.Role(this, "GatewayRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: "Role for AgentCore Gateway with comprehensive permissions",
    })

    // Lambda invoke permission
    toolLambda.grantInvoke(gatewayRole)

    // Bedrock permissions (region-agnostic)
    gatewayRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        resources: [
          "arn:aws:bedrock:*::foundation-model/*",
          `arn:aws:bedrock:*:${this.account}:inference-profile/*`,
        ],
      })
    )

    // SSM parameter access
    gatewayRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/${config.stack_name_base}/*`,
        ],
      })
    )

    // Cognito permissions
    gatewayRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["cognito-idp:DescribeUserPoolClient", "cognito-idp:InitiateAuth"],
        resources: [this.userPool.userPoolArn],
      })
    )

    // CloudWatch Logs
    gatewayRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock-agentcore/*`,
        ],
      })
    )

    // Load tool specification from JSON file
    const toolSpecPath = path.join(__dirname, "../../gateway/tools/sample_tool/tool_spec.json")
    const apiSpec = JSON.parse(require("fs").readFileSync(toolSpecPath, "utf8"))

    // Cognito OAuth2 configuration for gateway
    const cognitoIssuer = `https://cognito-idp.${this.region}.amazonaws.com/${this.userPool.userPoolId}`
    const cognitoDiscoveryUrl = `${cognitoIssuer}/.well-known/openid-configuration`

    // Create Gateway using L1 construct (CfnGateway)
    // This replaces the Custom Resource approach with native CloudFormation support
    const gateway = new bedrockagentcore.CfnGateway(this, "AgentCoreGateway", {
      name: `${config.stack_name_base}-gateway`,
      roleArn: gatewayRole.roleArn,
      protocolType: "MCP",
      protocolConfiguration: {
        mcp: {
          supportedVersions: ["2025-03-26"],
          // Optional: Enable semantic search for tools
          // searchType: "SEMANTIC",
        },
      },
      authorizerType: "CUSTOM_JWT",
      authorizerConfiguration: {
        customJwtAuthorizer: {
          allowedClients: [this.machineClient.userPoolClientId],
          discoveryUrl: cognitoDiscoveryUrl,
        },
      },
      description: "AgentCore Gateway with MCP protocol and JWT authentication",
    })

    // Create Gateway Target using L1 construct (CfnGatewayTarget)
    const gatewayTarget = new bedrockagentcore.CfnGatewayTarget(this, "GatewayTarget", {
      gatewayIdentifier: gateway.attrGatewayIdentifier,
      name: "sample-tool-target",
      description: "Sample tool Lambda target",
      targetConfiguration: {
        mcp: {
          lambda: {
            lambdaArn: toolLambda.functionArn,
            toolSchema: {
              inlinePayload: apiSpec,
            },
          },
        },
      },
      credentialProviderConfigurations: [
        {
          credentialProviderType: "GATEWAY_IAM_ROLE",
        },
      ],
    })

    // Ensure proper creation order
    gatewayTarget.addDependency(gateway)
    gateway.node.addDependency(toolLambda)
    gateway.node.addDependency(this.machineClient)
    gateway.node.addDependency(gatewayRole)

    // Store Gateway URL in SSM for runtime access
    new ssm.StringParameter(this, "GatewayUrlParam", {
      parameterName: `/${config.stack_name_base}/gateway_url`,
      stringValue: gateway.attrGatewayUrl,
      description: "AgentCore Gateway URL",
    })

    // Output gateway information
    new cdk.CfnOutput(this, "GatewayId", {
      value: gateway.attrGatewayIdentifier,
      description: "AgentCore Gateway ID",
    })

    new cdk.CfnOutput(this, "GatewayUrl", {
      value: gateway.attrGatewayUrl,
      description: "AgentCore Gateway URL",
    })

    new cdk.CfnOutput(this, "GatewayArn", {
      value: gateway.attrGatewayArn,
      description: "AgentCore Gateway ARN",
    })

    new cdk.CfnOutput(this, "GatewayTargetId", {
      value: gatewayTarget.ref,
      description: "AgentCore Gateway Target ID",
    })

    new cdk.CfnOutput(this, "ToolLambdaArn", {
      description: "ARN of the sample tool Lambda",
      value: toolLambda.functionArn,
    })
  }

  private createMachineAuthentication(config: AppConfig): void {
    // Create Resource Server for Machine-to-Machine (M2M) authentication
    // This defines the API scopes that machine clients can request access to
    const resourceServer = new cognito.UserPoolResourceServer(this, "ResourceServer", {
      userPool: this.userPool,
      identifier: `${config.stack_name_base}-gateway`,
      userPoolResourceServerName: `${config.stack_name_base}-gateway-resource-server`,
      scopes: [
        new cognito.ResourceServerScope({
          scopeName: "read",
          scopeDescription: "Read access to gateway",
        }),
        new cognito.ResourceServerScope({
          scopeName: "write",
          scopeDescription: "Write access to gateway",
        }),
      ],
    })

    // Create Machine Client for AgentCore Gateway authentication
    //
    // WHAT IS A MACHINE CLIENT?
    // A machine client is a Cognito User Pool Client configured for server-to-server authentication
    // using the OAuth2 Client Credentials flow. Unlike user-facing clients, it doesn't require
    // human interaction or user credentials.
    //
    // HOW IS IT DIFFERENT FROM THE REGULAR USER POOL CLIENT?
    // - Regular client: Uses Authorization Code flow for human users (frontend login)
    // - Machine client: Uses Client Credentials flow for service-to-service authentication
    // - Regular client: No client secret (public client for frontend security)
    // - Machine client: Has client secret (confidential client for backend security)
    // - Regular client: Scopes are openid, email, profile (user identity)
    // - Machine client: Scopes are custom resource server scopes (API permissions)
    //
    // WHY IS IT NEEDED?
    // The AgentCore Gateway needs to authenticate with Cognito to validate tokens and make
    // API calls on behalf of the system. The machine client provides the credentials for
    // this service-to-service authentication without requiring user interaction.
    this.machineClient = new cognito.UserPoolClient(this, "MachineClient", {
      userPool: this.userPool,
      userPoolClientName: `${config.stack_name_base}-machine-client`,
      generateSecret: true, // Required for client credentials flow
      oAuth: {
        flows: {
          clientCredentials: true, // Enable OAuth2 Client Credentials flow
        },
        scopes: [
          // Grant access to the resource server scopes defined above
          cognito.OAuthScope.resourceServer(
            resourceServer,
            new cognito.ResourceServerScope({
              scopeName: "read",
              scopeDescription: "Read access to gateway",
            })
          ),
          cognito.OAuthScope.resourceServer(
            resourceServer,
            new cognito.ResourceServerScope({
              scopeName: "write",
              scopeDescription: "Write access to gateway",
            })
          ),
        ],
      },
    })

    // Machine client must be created after resource server
    this.machineClient.node.addDependency(resourceServer)
  }

  /**
   * Recursively read directory contents and encode as base64.
   *
   * @param dirPath - Directory to read.
   * @param prefix - Prefix for file paths in output.
   * @param output - Output object to populate.
   */
  private readDirRecursive(dirPath: string, prefix: string, output: Record<string, string>): void {
    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
      const fullPath = path.join(dirPath, entry.name)
      const relativePath = path.join(prefix, entry.name)

      if (entry.isDirectory()) {
        // Skip __pycache__ directories
        if (entry.name !== "__pycache__") {
          this.readDirRecursive(fullPath, relativePath, output)
        }
      } else if (entry.isFile()) {
        const content = fs.readFileSync(fullPath)
        output[relativePath] = content.toString("base64")
      }
    }
  }

  /**
   * Create a hash of content for change detection.
   *
   * @param content - Content to hash.
   * @returns Hash string.
   */
  private hashContent(content: string): string {
    const crypto = require("crypto")
    return crypto.createHash("sha256").update(content).digest("hex").slice(0, 16)
  }

  /**
   * Extract agent metadata (tools, model ID, system prompt, and docstring) from agent Python source code.
   * Parses the agent file to extract the tools list, model_id configuration, system prompt, and function docstring.
   *
   * @param agentFilePath - Absolute path to the agent Python file
   * @returns Object containing tools array, modelId string, systemPrompt string, and longDescription string
   */
  private extractAgentMetadata(agentFilePath: string): {
      tools: string[]
      modelId: string
      systemPrompt: string
      longDescription: string
    } {
      try {
        const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')

        // Extract tools list from the agent file
        // Matches patterns like: tools = [tool1, tool2, ...]
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
        // Matches patterns like: model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
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

        // Long descriptions are generated by the post-deployment script (scripts/generate-agent-descriptions.ts)
        // which uses an LLM to create user-friendly descriptions from agent docstrings and system prompts.
        // During CDK deployment, we store an empty string as a placeholder.
        const longDescription = ''

        return { tools, modelId, systemPrompt, longDescription }
      } catch (error) {
        console.warn(`Failed to extract metadata from ${agentFilePath}:`, error)
        return { tools: [], modelId: 'unknown', systemPrompt: '', longDescription: '' }
      }
    }

  /**
   * Upload agent source code to S3 bucket.
   * Uses BucketDeployment to upload the source code file to S3 with a structured key.
   *
   * @param bucket - S3 bucket for agent source code storage
   * @param agentName - Name of the agent
   * @param sourceCode - Agent Python source code content
   * @returns S3 URL in format: s3://{bucketName}/{key}
   */
  private uploadAgentSourceToS3(
    bucket: s3.Bucket,
    agentName: string,
    sourceCode: string
  ): string {
    const s3Key = `agents/${agentName}/${agentName}_agent.py`

    new s3deploy.BucketDeployment(this, `AgentSourceDeploy-${agentName}`, {
      sources: [s3deploy.Source.data(s3Key, sourceCode)],
      destinationBucket: bucket,
      prune: false,
    })

    return `s3://${bucket.bucketName}/${s3Key}`
  }



  /**
   * Creates multiple AgentCore Runtimes for multi-agent orchestration patterns.
   * Reads agents.json manifest and deploys a separate runtime for each agent.
   * Implements graceful degradation - continues deployment even if individual agents fail.
   * 
   * @param config - Application configuration
   * @param pattern - Pattern name (e.g., "strands-multi-agent-orchestrator")
   * @param patternPath - Absolute path to pattern directory
   */
  private createMultiAgentRuntimes(
    config: AppConfig,
    pattern: string,
    patternPath: string
  ): void {
    const stack = cdk.Stack.of(this)
    const deploymentType = config.backend.deployment_type

    // Load and validate agent manifest
    const manifest = loadAgentManifest(patternPath)

    // Create shared resources ONCE (outside agent loop)
    const sharedResources = this.createSharedAgentResources(config)

    // Store runtime ARNs for cross-agent invocation
    const runtimeArns: { [agentName: string]: string } = {}
    const deploymentStatuses: { [agentName: string]: "success" | "failed" } = {}

    // Create runtime for each agent with error handling
    for (const agentEntry of manifest.agents) {
      const agentName = agentEntry.name

      try {
        // Validate agent directory and Dockerfile exist
        const agentDir = path.join(patternPath, "agents", agentName)
        const dockerfilePath = path.join(agentDir, "Dockerfile")

        if (!fs.existsSync(agentDir)) {
          throw new Error(
            `Agent directory not found: ${agentDir}. ` +
              `Manifest references agent "${agentName}" but directory does not exist.`
          )
        }

        if (deploymentType === "docker" && !fs.existsSync(dockerfilePath)) {
          throw new Error(
            `Dockerfile not found: ${dockerfilePath}. ` +
              `Agent "${agentName}" must have a Dockerfile for Docker deployment.`
          )
        }

        // Create agent-specific runtime
        const runtime = this.createAgentRuntime(
          config,
          pattern,
          agentEntry,
          sharedResources,
          deploymentType
        )

        // Store runtime ARN
        runtimeArns[agentName] = runtime.agentRuntimeArn
        deploymentStatuses[agentName] = "success"

        // Store agent metadata in SSM
        this.storeAgentMetadata(config, pattern, agentEntry, runtime, "success", sharedResources)

        // Create CloudFormation outputs
        this.createAgentOutputs(config, agentEntry, runtime, "success")

        console.log(`✅ Successfully deployed agent: ${agentName}`)
      } catch (error: any) {
        // Log error but continue with other agents (graceful degradation)
        console.error(`❌ Failed to deploy agent ${agentName}:`, error)
        deploymentStatuses[agentName] = "failed"

        // Store failure status in SSM
        this.storeAgentFailureMetadata(config, agentEntry, error.message)

        // Create failure output
        this.createAgentFailureOutputs(config, agentEntry, error.message)

        // Add warning annotation to CloudFormation
        cdk.Annotations.of(this).addWarning(
          `Agent ${agentName} failed to deploy: ${error.message}`
        )
      }
    }

    // Check if at least one agent deployed successfully
    const successfulAgents = Object.entries(deploymentStatuses).filter(
      ([_, status]) => status === "success"
    )

    if (successfulAgents.length === 0) {
      throw new Error(
        "All agents failed to deploy. At least one agent must deploy successfully."
      )
    }

    // Store the default runtime ARN (or first successful agent)
    const defaultAgent =
      manifest.agents.find((a) => a.isDefault && deploymentStatuses[a.name] === "success") ||
      manifest.agents.find((a) => deploymentStatuses[a.name] === "success")!

    this.runtimeArn = runtimeArns[defaultAgent.name]

    // Create summary output
    new cdk.CfnOutput(this, "DeploymentSummary", {
      description: "Multi-agent deployment summary",
      value: JSON.stringify({
        total: manifest.agents.length,
        successful: successfulAgents.length,
        failed: manifest.agents.length - successfulAgents.length,
        agents: deploymentStatuses,
      }),
    })
  }

  /**
   * Creates shared backend resources used by all agents.
   * These resources are created once and shared across all agent runtimes.
   * 
   * @param config - Application configuration
   * @returns Shared resources object containing memory, role, and related ARNs
   */
  private createSharedAgentResources(config: AppConfig): SharedAgentResources {
    // Create AgentCore execution role
    const agentRole = new AgentCoreRole(this, "AgentCoreRole")

    // Create memory resource with long-term memory strategies
    const memory = new cdk.CfnResource(this, "AgentMemory", {
      type: "AWS::BedrockAgentCore::Memory",
      properties: {
        Name: cdk.Names.uniqueResourceName(this, { maxLength: 48 }),
        EventExpiryDuration: 30,
        Description: `Memory with long-term strategies for ${config.stack_name_base}`,
        MemoryStrategies: [
          {
            SummaryMemoryStrategy: {
              Name: "SessionSummarizer",
              Namespaces: ["/summaries/{actorId}/{sessionId}"],
            },
          },
          {
            UserPreferenceMemoryStrategy: {
              Name: "PreferenceLearner",
              Namespaces: ["/preferences/{actorId}"],
            },
          },
          {
            SemanticMemoryStrategy: {
              Name: "FactExtractor",
              Namespaces: ["/facts/{actorId}"],
            },
          },
        ],
        MemoryExecutionRoleArn: agentRole.roleArn,
        Tags: {
          Name: `${config.stack_name_base}_Memory`,
          ManagedBy: "CDK",
        },
      },
    })

    const memoryId = memory.getAtt("MemoryId").toString()
    const memoryArn = memory.getAtt("MemoryArn").toString()

    // Store the memory ARN for access from main stack
    this.memoryArn = memoryArn

    // Add memory-specific permissions to agent role
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "MemoryResourceAccess",
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:ListEvents",
          "bedrock-agentcore:RetrieveMemoryRecords",
        ],
        resources: [memoryArn],
      })
    )

    // Add SSM permissions for Gateway URL lookup
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "SSMParameterAccess",
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/${config.stack_name_base}/*`,
        ],
      })
    )

    // Add Code Interpreter permissions
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        sid: "CodeInterpreterAccess",
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock-agentcore:StartCodeInterpreterSession",
          "bedrock-agentcore:StopCodeInterpreterSession",
          "bedrock-agentcore:InvokeCodeInterpreter",
        ],
        resources: [`arn:aws:bedrock-agentcore:${this.region}:aws:code-interpreter/*`],
      })
    )

    // Create S3 bucket for agent source code
    const agentSourceCodeBucket = new s3.Bucket(this, "AgentSourceCodeBucket", {
      bucketName: `${config.stack_name_base}-agent-source-code`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      versioned: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
    })

    // Output memory ARN
    new cdk.CfnOutput(this, "MemoryArn", {
      description: "ARN of the shared agent memory resource",
      value: memoryArn,
    })

    return {
      memory,
      memoryId,
      memoryArn,
      agentRole,
      agentSourceCodeBucket,
    }
  }

  /**
   * Creates a single AgentCore Runtime for one agent in a multi-agent pattern.
   * 
   * @param config - Application configuration
   * @param pattern - Pattern name
   * @param agentEntry - Agent metadata from manifest
   * @param sharedResources - Shared resources (memory, role)
   * @param deploymentType - Deployment type (docker or zip)
   * @returns Created runtime instance
   */
  private createAgentRuntime(
    config: AppConfig,
    pattern: string,
    agentEntry: AgentManifestEntry,
    sharedResources: SharedAgentResources,
    deploymentType: string
  ): agentcore.Runtime {
    const stack = cdk.Stack.of(this)
    const agentName = agentEntry.name

    // Create agent-specific runtime artifact
    let agentRuntimeArtifact: agentcore.AgentRuntimeArtifact

    if (deploymentType === "zip") {
      // ZIP deployment for this agent
      throw new Error("ZIP deployment not yet implemented for multi-agent patterns")
    } else {
      // Docker deployment for this agent
      agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
        path.resolve(__dirname, "..", ".."),
        {
          platform: ecr_assets.Platform.LINUX_ARM64,
          file: `patterns/${pattern}/agents/${agentName}/Dockerfile`,
        }
      )
    }

    // Configure network mode (default to public)
    const networkConfiguration = agentcore.RuntimeNetworkConfiguration.usingPublicNetwork()

    // Configure JWT authorizer with Cognito
    const authorizerConfiguration = agentcore.RuntimeAuthorizerConfiguration.usingJWT(
      `https://cognito-idp.${stack.region}.amazonaws.com/${this.userPoolId}/.well-known/openid-configuration`,
      [this.userPoolClientId]
    )

    // Environment variables for the runtime
    const envVars: { [key: string]: string } = {
      AWS_REGION: stack.region,
      AWS_DEFAULT_REGION: stack.region,
      MEMORY_ID: sharedResources.memoryId,
      STACK_NAME: config.stack_name_base,
      AGENT_NAME: agentName, // Agent can use this to identify itself
    }

    // Create the runtime
    const runtime = new agentcore.Runtime(this, `Runtime-${agentName}`, {
      runtimeName: `${config.stack_name_base.replace(/-/g, "_")}_${agentName}`,
      agentRuntimeArtifact: agentRuntimeArtifact,
      executionRole: sharedResources.agentRole,
      networkConfiguration: networkConfiguration,
      protocolConfiguration: agentcore.ProtocolType.HTTP,
      environmentVariables: envVars,
      authorizerConfiguration: authorizerConfiguration,
      requestHeaderConfiguration: {
        allowlistedHeaders: ["Authorization"],
      },
      description: `${agentEntry.displayName} - ${agentEntry.description}`,
    })

    return runtime
  }

  /**
   * Stores agent metadata in SSM Parameter Store for runtime discovery.
   * Used by backend services and will be used by frontend in Task 8.
   * 
   * @param config - Application configuration
   * @param pattern - Agent pattern type (e.g., 'strands-multi-agent-orchestrator')
   * @param agentEntry - Agent metadata from manifest
   * @param runtime - Created runtime instance
   * @param status - Deployment status ('success' or 'failed')
   */
  /**
     * Stores agent metadata in SSM Parameter Store for runtime discovery.
     * Used by backend services and will be used by frontend in Task 8.
     * 
     * @param config - Application configuration
     * @param pattern - Agent pattern type (e.g., 'strands-multi-agent-orchestrator')
     * @param agentEntry - Agent metadata from manifest
     * @param runtime - Created runtime instance
     * @param status - Deployment status ('success' or 'failed')
     * @param sharedResources - Shared resources including S3 bucket for source code
     */
    private storeAgentMetadata(
      config: AppConfig,
      pattern: string,
      agentEntry: AgentManifestEntry,
      runtime: agentcore.Runtime,
      status: "success" | "failed",
      sharedResources: SharedAgentResources
    ): void {
      const agentName = agentEntry.name
      const baseParam = `/${config.stack_name_base}/agents/${agentName}`

      // Extract metadata from agent source file
      const patternPath = path.resolve(__dirname, "..", "..", "patterns", pattern)
      const agentFilePath = path.join(patternPath, "agents", agentName, `${agentName}_agent.py`)

      let metadata: { tools: string[]; modelId: string; systemPrompt: string; longDescription: string } = { 
        tools: [], 
        modelId: 'unknown',
        systemPrompt: '',
        longDescription: ''
      }
      let sourceCodeUrl = ''

      try {
        if (fs.existsSync(agentFilePath)) {
          metadata = this.extractAgentMetadata(agentFilePath)
          const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')
          sourceCodeUrl = this.uploadAgentSourceToS3(
            sharedResources.agentSourceCodeBucket,
            agentName,
            sourceCode
          )
        } else {
          console.warn(`Agent file not found: ${agentFilePath}`)
        }
      } catch (error) {
        console.warn(`Failed to process metadata for ${agentName}:`, error)
      }

      // Runtime ARN
      new ssm.StringParameter(this, `SSMAgentRuntimeArn-${agentName}`, {
        parameterName: `${baseParam}/runtime-arn`,
        stringValue: runtime.agentRuntimeArn,
        description: `Runtime ARN for ${agentEntry.displayName}`,
      })

      // Runtime ID
      new ssm.StringParameter(this, `SSMAgentRuntimeId-${agentName}`, {
        parameterName: `${baseParam}/runtime-id`,
        stringValue: runtime.agentRuntimeId,
        description: `Runtime ID for ${agentEntry.displayName}`,
      })

      // Display name
      new ssm.StringParameter(this, `SSMAgentDisplayName-${agentName}`, {
        parameterName: `${baseParam}/display-name`,
        stringValue: agentEntry.displayName,
        description: `Display name for ${agentName} agent`,
      })

      // Description
      new ssm.StringParameter(this, `SSMAgentDescription-${agentName}`, {
        parameterName: `${baseParam}/description`,
        stringValue: agentEntry.description,
        description: `Description for ${agentName} agent`,
      })

      // Is default flag
      new ssm.StringParameter(this, `SSMAgentIsDefault-${agentName}`, {
        parameterName: `${baseParam}/is-default`,
        stringValue: agentEntry.isDefault.toString(),
        description: `Whether ${agentName} is the default agent`,
      })

      // Pattern
      new ssm.StringParameter(this, `SSMAgentPattern-${agentName}`, {
        parameterName: `${baseParam}/pattern`,
        stringValue: pattern,
        description: `Pattern type for ${agentName} agent`,
      })

      // Deployment status
      new ssm.StringParameter(this, `SSMAgentStatus-${agentName}`, {
        parameterName: `${baseParam}/status`,
        stringValue: status,
        description: `Deployment status for ${agentName} agent`,
      })

      // Tools list (extracted from agent source)
      new ssm.StringParameter(this, `SSMAgentTools-${agentName}`, {
        parameterName: `${baseParam}/tools`,
        stringValue: JSON.stringify(metadata.tools),
        description: `Tools for ${agentName}`,
      })

      // Model ID (extracted from agent source)
      new ssm.StringParameter(this, `SSMAgentModel-${agentName}`, {
        parameterName: `${baseParam}/model`,
        stringValue: metadata.modelId,
        description: `Model for ${agentName}`,
      })

      // Source code URL (S3 location)
      if (sourceCodeUrl) {
        new ssm.StringParameter(this, `SSMAgentSourceCodeUrl-${agentName}`, {
          parameterName: `${baseParam}/source-code-url`,
          stringValue: sourceCodeUrl,
          description: `S3 URL for ${agentName} source`,
        })
      }

      // System prompt (extracted from agent source)
      new ssm.StringParameter(this, `SSMAgentSystemPrompt-${agentName}`, {
        parameterName: `${baseParam}/system-prompt`,
        stringValue: metadata.systemPrompt,
        description: `System prompt for ${agentName}`,
      })

      // Long description (generated from docstring)
      new ssm.StringParameter(this, `SSMAgentLongDescription-${agentName}`, {
        parameterName: `${baseParam}/long-description`,
        stringValue: metadata.longDescription,
        description: `Long description for ${agentName}`,
      })
    }

  /**
   * Stores failure metadata for agents that failed to deploy.
   * 
   * @param config - Application configuration
   * @param agentEntry - Agent metadata from manifest
   * @param errorMessage - Error message from deployment failure
   */
  private storeAgentFailureMetadata(
    config: AppConfig,
    agentEntry: AgentManifestEntry,
    errorMessage: string
  ): void {
    const agentName = agentEntry.name
    const baseParam = `/${config.stack_name_base}/agents/${agentName}`

    // Deployment status
    new ssm.StringParameter(this, `SSMAgentStatus-${agentName}`, {
      parameterName: `${baseParam}/status`,
      stringValue: "failed",
      description: `Deployment status for ${agentName} agent`,
    })

    // Error message (truncate to SSM limit)
    new ssm.StringParameter(this, `SSMAgentError-${agentName}`, {
      parameterName: `${baseParam}/error`,
      stringValue: errorMessage.substring(0, 4096), // SSM limit
      description: `Error message for failed ${agentName} agent deployment`,
    })

    // Display name (for UI to show failed agent)
    new ssm.StringParameter(this, `SSMAgentDisplayName-${agentName}`, {
      parameterName: `${baseParam}/display-name`,
      stringValue: agentEntry.displayName,
      description: `Display name for ${agentName} agent`,
    })
  }

  /**
   * Creates CloudFormation outputs for agent runtime information.
   * 
   * @param config - Application configuration
   * @param agentEntry - Agent metadata from manifest
   * @param runtime - Created runtime instance
   * @param status - Deployment status
   */
  private createAgentOutputs(
    config: AppConfig,
    agentEntry: AgentManifestEntry,
    runtime: agentcore.Runtime,
    status: "success" | "failed"
  ): void {
    const agentName = agentEntry.name

    new cdk.CfnOutput(this, `OutputAgentRuntimeArn-${agentName}`, {
      description: `ARN of ${agentEntry.displayName} runtime`,
      value: runtime.agentRuntimeArn,
      exportName: `${config.stack_name_base}-AgentRuntimeArn-${agentName}`,
    })

    new cdk.CfnOutput(this, `OutputAgentRuntimeId-${agentName}`, {
      description: `ID of ${agentEntry.displayName} runtime`,
      value: runtime.agentRuntimeId,
      exportName: `${config.stack_name_base}-AgentRuntimeId-${agentName}`,
    })

    new cdk.CfnOutput(this, `OutputAgentStatus-${agentName}`, {
      description: `Deployment status of ${agentEntry.displayName}`,
      value: status,
      exportName: `${config.stack_name_base}-AgentStatus-${agentName}`,
    })
  }

  /**
   * Creates CloudFormation outputs for failed agent deployments.
   * 
   * @param config - Application configuration
   * @param agentEntry - Agent metadata from manifest
   * @param errorMessage - Error message from deployment failure
   */
  private createAgentFailureOutputs(
    config: AppConfig,
    agentEntry: AgentManifestEntry,
    errorMessage: string
  ): void {
    const agentName = agentEntry.name

    new cdk.CfnOutput(this, `OutputAgentStatus-${agentName}`, {
      description: `Deployment status of ${agentEntry.displayName}`,
      value: "failed",
      exportName: `${config.stack_name_base}-AgentStatus-${agentName}`,
    })

    new cdk.CfnOutput(this, `OutputAgentError-${agentName}`, {
      description: `Error for ${agentEntry.displayName}`,
      value: errorMessage.substring(0, 200), // CloudFormation output limit
      exportName: `${config.stack_name_base}-AgentError-${agentName}`,
    })
  }
}

/**
 * Shared resources used by all agents in multi-agent patterns.
 */
interface SharedAgentResources {
  /** Memory resource instance */
  memory: cdk.CfnResource
  /** Memory ID for environment variables */
  memoryId: string
  /** Memory ARN for IAM permissions */
  memoryArn: string
  /** Shared execution role for all agents */
  agentRole: AgentCoreRole
  /** S3 bucket for agent source code storage */
  agentSourceCodeBucket: s3.Bucket
}
