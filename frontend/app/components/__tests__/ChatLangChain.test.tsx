import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatLangChain from '../ChatLangChain'
import { useGraphContext } from '@/app/contexts/GraphContext'
import { usePermissions } from '@/app/hooks/usePermissions'
import { useToast } from '@/app/hooks/use-toast'
import { useQueryState } from 'nuqs'

// Mock dependencies
jest.mock('@/app/contexts/GraphContext')
jest.mock('@/app/hooks/usePermissions')
jest.mock('@/app/hooks/use-toast')
jest.mock('nuqs')
jest.mock('@assistant-ui/react', () => ({
  AssistantRuntimeProvider: ({ children }: any) => <div>{children}</div>,
  useExternalStoreRuntime: jest.fn(() => ({})),
  useExternalMessageConverter: jest.fn(() => ({ convertMessage: jest.fn() })),
}))

// Mock components
jest.mock('../chat-interface', () => ({
  ThreadChat: ({ onNew }: any) => (
    <div data-testid="thread-chat">
      <button onClick={() => onNew({ content: [{ type: 'text', text: 'Test message' }] })}>
        Send Message
      </button>
    </div>
  ),
}))

jest.mock('../SelectModel', () => ({
  SelectModel: () => <div data-testid="select-model">Model Selector</div>,
}))

jest.mock('../thread-history', () => ({
  ThreadHistory: () => <div data-testid="thread-history">Thread History</div>,
}))

const mockGraphContext = {
  threadsData: {
    getUserThreads: jest.fn().mockResolvedValue([]),
    createThread: jest.fn().mockResolvedValue({ id: 'new-thread-id' }),
    getThreadById: jest.fn().mockResolvedValue(null),
  },
  userData: {
    userId: 'test-user-id',
  },
  graphData: {
    messages: [],
    setMessages: jest.fn(),
    streamMessage: jest.fn(),
    switchSelectedThread: jest.fn(),
  },
}

const mockPermissions = {
  canCreateThreads: true,
  canDeleteOwnThreads: true,
  canViewTeamThreads: false,
  canExportData: false,
  canManageTeam: false,
  maxThreadsPerDay: 50,
  allowedAgents: ['chat', 'search'],
  allowedDataSources: ['public', 'company_wide'],
  customPermissions: {},
}

describe('ChatLangChain', () => {
  const mockToast = jest.fn()
  const mockSetThreadId = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useGraphContext as jest.Mock).mockReturnValue(mockGraphContext)
    ;(usePermissions as jest.Mock).mockReturnValue({
      permissions: mockPermissions,
      loading: false,
      hasAgent: jest.fn().mockReturnValue(true),
    })
    ;(useToast as jest.Mock).mockReturnValue({ toast: mockToast })
    ;(useQueryState as jest.Mock).mockReturnValue(['thread-123', mockSetThreadId])
  })

  it('should render all main components', () => {
    render(<ChatLangChain />)

    expect(screen.getByTestId('select-model')).toBeInTheDocument()
    expect(screen.getByTestId('thread-chat')).toBeInTheDocument()
    expect(screen.getByTestId('thread-history')).toBeInTheDocument()
  })

  it('should load thread from URL parameter on mount', async () => {
    const mockThread = { id: 'thread-123', name: 'Test Thread' }
    mockGraphContext.threadsData.getThreadById.mockResolvedValueOnce(mockThread)

    render(<ChatLangChain />)

    await waitFor(() => {
      expect(mockGraphContext.threadsData.getThreadById).toHaveBeenCalledWith('thread-123')
      expect(mockGraphContext.graphData.switchSelectedThread).toHaveBeenCalledWith(mockThread)
    })
  })

  it('should clear thread ID if thread not found', async () => {
    mockGraphContext.threadsData.getThreadById.mockResolvedValueOnce(null)

    render(<ChatLangChain />)

    await waitFor(() => {
      expect(mockGraphContext.threadsData.getThreadById).toHaveBeenCalledWith('thread-123')
      expect(mockSetThreadId).toHaveBeenCalledWith(null)
    })
  })

  it('should handle new message submission', async () => {
    ;(useQueryState as jest.Mock).mockReturnValue([null, mockSetThreadId])
    
    mockGraphContext.graphData.streamMessage.mockResolvedValueOnce({
      messages: ['Response message'],
    })

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockGraphContext.threadsData.createThread).toHaveBeenCalled()
      expect(mockGraphContext.graphData.streamMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          messages: expect.arrayContaining([
            expect.objectContaining({
              content: 'Test message',
            }),
          ]),
        })
      )
    })
  })

  it('should disable submission when user is not authenticated', () => {
    ;(useGraphContext as jest.Mock).mockReturnValue({
      ...mockGraphContext,
      userData: { userId: null },
    })

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    expect(mockToast).toHaveBeenCalledWith({
      title: "Authentication Required",
      description: "Please sign in to send messages",
      variant: "destructive",
    })
    expect(mockGraphContext.graphData.streamMessage).not.toHaveBeenCalled()
  })

  it('should disable submission when permissions are loading', () => {
    ;(usePermissions as jest.Mock).mockReturnValue({
      permissions: null,
      loading: true,
      hasAgent: jest.fn(),
    })

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    expect(mockToast).toHaveBeenCalledWith({
      title: "Authentication Required",
      description: "Please sign in to send messages",
      variant: "destructive",
    })
  })

  it('should disable submission when user cannot create threads', () => {
    ;(usePermissions as jest.Mock).mockReturnValue({
      permissions: { ...mockPermissions, canCreateThreads: false },
      loading: false,
      hasAgent: jest.fn(),
    })

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    expect(mockToast).toHaveBeenCalledWith({
      title: "Authentication Required",
      description: "Please sign in to send messages",
      variant: "destructive",
    })
  })

  it('should handle stream message errors', async () => {
    ;(useQueryState as jest.Mock).mockReturnValue([null, mockSetThreadId])
    
    const mockError = new Error('Stream failed')
    mockGraphContext.graphData.streamMessage.mockRejectedValueOnce(mockError)

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "An error occurred",
        description: mockError.message,
        variant: "destructive",
      })
    })
  })

  it('should append message to existing thread', async () => {
    // Simulate existing thread
    mockGraphContext.graphData.messages = [
      { id: '1', content: 'Previous message' },
    ]
    
    mockGraphContext.graphData.streamMessage.mockResolvedValueOnce({
      messages: ['Response'],
    })

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockGraphContext.threadsData.createThread).not.toHaveBeenCalled()
      expect(mockGraphContext.graphData.streamMessage).toHaveBeenCalled()
    })
  })

  it('should handle thread creation failure', async () => {
    ;(useQueryState as jest.Mock).mockReturnValue([null, mockSetThreadId])
    
    mockGraphContext.threadsData.createThread.mockRejectedValueOnce(
      new Error('Failed to create thread')
    )

    render(<ChatLangChain />)

    const sendButton = screen.getByText('Send Message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "An error occurred",
        description: "Failed to create thread",
        variant: "destructive",
      })
    })
  })

  it('should not render debug info in production', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'

    render(<ChatLangChain />)

    expect(screen.queryByText(/API_URL:/)).not.toBeInTheDocument()

    process.env.NODE_ENV = originalEnv
  })

  it('should render debug info in development', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'

    render(<ChatLangChain />)

    expect(screen.getByText(/API_URL:/)).toBeInTheDocument()
    expect(screen.getByText(/ENV: development/)).toBeInTheDocument()

    process.env.NODE_ENV = originalEnv
  })
})