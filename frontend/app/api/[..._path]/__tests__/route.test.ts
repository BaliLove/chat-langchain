import { NextRequest } from 'next/server'
import { GET, POST, PUT, PATCH, DELETE, OPTIONS } from '../route'

// Mock fetch globally
global.fetch = jest.fn()

describe('API Proxy Route', () => {
  const originalEnv = process.env

  beforeEach(() => {
    jest.clearAllMocks()
    // Reset environment variables
    process.env = {
      ...originalEnv,
      API_BASE_URL: 'https://api.example.com',
      LANGSMITH_API_KEY: 'test-api-key',
    }
  })

  afterEach(() => {
    process.env = originalEnv
  })

  describe('GET requests', () => {
    it('should proxy GET requests correctly', async () => {
      const mockResponse = new Response(JSON.stringify({ data: 'test' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads/123', {
        method: 'GET',
      })

      const response = await GET(request)
      
      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads/123',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'x-api-key': 'test-api-key',
          }),
        })
      )

      const responseData = await response.json()
      expect(responseData).toEqual({ data: 'test' })
      expect(response.status).toBe(200)
    })

    it('should handle query parameters', async () => {
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest(
        'http://localhost:3000/api/threads?limit=10&offset=20',
        { method: 'GET' }
      )

      await GET(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads?limit=10&offset=20',
        expect.any(Object)
      )
    })

    it('should remove internal query parameters', async () => {
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest(
        'http://localhost:3000/api/threads?_path=test&nxtP_path=test2&limit=10',
        { method: 'GET' }
      )

      await GET(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads?limit=10',
        expect.any(Object)
      )
    })
  })

  describe('POST requests', () => {
    it('should proxy POST requests with body', async () => {
      const mockResponse = new Response(JSON.stringify({ id: '123' }), {
        status: 201,
      })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const body = JSON.stringify({ message: 'Hello' })
      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'POST',
        body,
      })

      const response = await POST(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads',
        expect.objectContaining({
          method: 'POST',
          body,
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'x-api-key': 'test-api-key',
          }),
        })
      )

      expect(response.status).toBe(201)
    })
  })

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      ;(fetch as jest.Mock).mockRejectedValue(new Error('Network error'))

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      const response = await GET(request)
      const responseData = await response.json()

      expect(response.status).toBe(500)
      expect(responseData).toEqual({
        error: 'Network error',
        details: {
          path: 'threads',
          apiBaseUrl: 'https://api.example.com',
          hasApiKey: true,
        },
      })
    })

    it('should handle missing API key', async () => {
      delete process.env.LANGSMITH_API_KEY
      
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      await GET(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'x-api-key': expect.any(String),
          }),
        })
      )
    })
  })

  describe('Retry logic', () => {
    it('should retry on retryable status codes', async () => {
      // First attempt: 503
      ;(fetch as jest.Mock).mockResolvedValueOnce(
        new Response('Service unavailable', { status: 503 })
      )
      // Second attempt: 502
      ;(fetch as jest.Mock).mockResolvedValueOnce(
        new Response('Bad gateway', { status: 502 })
      )
      // Third attempt: Success
      ;(fetch as jest.Mock).mockResolvedValueOnce(
        new Response('{}', { status: 200 })
      )

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      const response = await GET(request)

      expect(fetch).toHaveBeenCalledTimes(3)
      expect(response.status).toBe(200)
    })

    it('should stop retrying on non-retryable status codes', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce(
        new Response('Not found', { status: 404 })
      )

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      const response = await GET(request)

      expect(fetch).toHaveBeenCalledTimes(1)
      expect(response.status).toBe(404)
    })

    it('should exhaust retries and return last error', async () => {
      // All attempts fail with 503
      ;(fetch as jest.Mock).mockResolvedValue(
        new Response('Service unavailable', { status: 503 })
      )

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      const response = await GET(request)

      expect(fetch).toHaveBeenCalledTimes(4) // Initial + 3 retries
      expect(response.status).toBe(503)
    })
  })

  describe('CORS headers', () => {
    it('should add CORS headers to responses', async () => {
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads', {
        method: 'GET',
      })

      const response = await GET(request)

      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*')
      expect(response.headers.get('Access-Control-Allow-Methods')).toBe(
        'GET, POST, PUT, PATCH, DELETE, OPTIONS'
      )
      expect(response.headers.get('Access-Control-Allow-Headers')).toBe('*')
    })

    it('should handle OPTIONS requests', async () => {
      const response = await OPTIONS()

      expect(response.status).toBe(204)
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*')
    })
  })

  describe('Other HTTP methods', () => {
    it('should handle PUT requests', async () => {
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads/123', {
        method: 'PUT',
        body: JSON.stringify({ data: 'updated' }),
      })

      await PUT(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads/123',
        expect.objectContaining({ method: 'PUT' })
      )
    })

    it('should handle PATCH requests', async () => {
      const mockResponse = new Response('{}', { status: 200 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads/123', {
        method: 'PATCH',
        body: JSON.stringify({ data: 'patched' }),
      })

      await PATCH(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads/123',
        expect.objectContaining({ method: 'PATCH' })
      )
    })

    it('should handle DELETE requests', async () => {
      const mockResponse = new Response('', { status: 204 })
      ;(fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const request = new NextRequest('http://localhost:3000/api/threads/123', {
        method: 'DELETE',
      })

      await DELETE(request)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/threads/123',
        expect.objectContaining({ method: 'DELETE' })
      )
    })
  })
})