def console_chat(agent, description=None):
    """
    Interactive console chat with an agent.
    
    Args:
        agent: The agent to chat with
        description: Optional description to display at startup
    """
    
    print("\n" + "=" * 70)
    print('Welcome to a simple "Console Chat" with an agent ...')
    print("=" * 70 + "\n")
    
    # Print agent description if provided
    if description:
        print(f"\n🤖 {description}\n")
    
    print("\nType 'exit', 'bye', or 'quit' to end the session\n")

    while True:
        try:
            userMsg = input("\nUser > ")
        
            if userMsg.lower() in ['exit', 'bye', 'quit']:
                print("Goodbye\n")
                break
            else:
                print("\nAgent > ", end="")
                agent(userMsg)
                print("\n")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye\n")
            break
        except Exception as e:
            print(f"\n\nError: {str(e)}")
