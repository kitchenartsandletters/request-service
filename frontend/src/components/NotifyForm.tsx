import { useState } from 'react'
import React from 'react'

const NotifyForm = () => {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  // Using constants for now — you can pass these in as props later
  const product_id = 12345
  const product_title = "The Book of Ferments"

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')

    try {
      const res = await fetch('/api/interest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, product_id, product_title })
      })

      if (!res.ok) throw new Error('Failed to submit request.')

      const data = await res.json()
      if (data.success) {
        setStatus('success')
        setMessage('You’ll be notified when this item is back in stock.')
      } else {
        throw new Error('Unexpected response.')
      }
    } catch (err: any) {
      setStatus('error')
      setMessage(err.message || 'Something went wrong.')
    }
  }

  return (
    <div className="product-form__line-item-field mt-4">
      <form onSubmit={handleSubmit} className="product-form__notify-form">
        <label className="block text-sm font-medium mb-1" htmlFor="notify-email">
          Notify me when available
        </label>
        <div className="flex items-center space-x-2">
          <input
            id="notify-email"
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={status === 'loading'}
            className="bg-black text-white text-sm px-4 py-2 rounded hover:bg-gray-800 transition"
          >
            {status === 'loading' ? 'Submitting...' : 'Notify Me'}
          </button>
        </div>
      </form>
      {status === 'success' && (
        <p className="text-green-600 text-sm mt-2">{message}</p>
      )}
      {status === 'error' && (
        <p className="text-red-600 text-sm mt-2">{message}</p>
      )}
    </div>
  )
}

export default NotifyForm
