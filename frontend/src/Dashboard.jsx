import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { translations } from './translations.js'
import './Dashboard.css'

// In local dev this falls back to localhost:8000. Once deployed,
// set VITE_API_BASE in your hosting platform's environment variables
// to your real backend URL — Vite bakes env vars in at build time.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function Dashboard() {
  // useParams() reads the ":slug" part of the URL that React Router
  // matched in App.jsx. If the URL is /dashboard/biz_a8f3k2, then
  // slug === "biz_a8f3k2" here.
  const { slug } = useParams()

  // React state: whenever these change, the component re-renders.
  // This is the core React mental model you'll use everywhere.
  const [businessName, setBusinessName] = useState('')
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [copiedId, setCopiedId] = useState(null)
  const [lang, setLang] = useState('en')

  const t = (key) => translations[lang][key]

  // Fetches whatever is already saved in the DB. Fast, no external
  // API calls on the backend side — good for the initial page load.
  async function loadReviews() {
    try {
      const res = await fetch(`${API_BASE}/api/businesses/${slug}/reviews`)
      if (!res.ok) throw new Error('Could not load this dashboard')
      const data = await res.json()
      setBusinessName(data.business_name)
      setReviews(data.reviews)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Tells the backend to go pull fresh reviews from Google and draft
  // any new ones with Claude. Slower (hits two external APIs), so we
  // show a distinct "refreshing" state rather than reusing "loading".
  async function handleRefresh() {
    setRefreshing(true)
    try {
      await fetch(`${API_BASE}/api/businesses/${slug}/refresh`, { method: 'POST' })
      await loadReviews() // re-fetch so the UI shows whatever's new
    } catch (err) {
      setError('Refresh failed — try again in a moment.')
    } finally {
      setRefreshing(false)
    }
  }

  // useEffect with [slug] as the dependency: this runs once when the
  // component first appears, and again if the slug ever changes.
  // This is the standard "fetch data when the page loads" pattern.
  useEffect(() => {
    loadReviews()
  }, [slug])

  function handleDraftEdit(reviewId, newText) {
    setReviews(prev =>
      prev.map(r => (r.id === reviewId ? { ...r, drafted_response: newText } : r))
    )
  }

  async function handleSaveDraft(reviewId, text) {
    await fetch(`${API_BASE}/api/reviews/${reviewId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: new URLSearchParams({ drafted_response: text }),
    })
  }

  function handleCopy(reviewId, text) {
    navigator.clipboard.writeText(text)
    setCopiedId(reviewId)
    setTimeout(() => setCopiedId(null), 1500)
  }

  if (loading) return <div className="dash-state">{t('loading')}</div>
  if (error) return <div className="dash-state dash-error">{error}</div>

  return (
    <div className="dash">
      <div className="lang-switch">
        {['uz', 'ru', 'en'].map((code) => (
          <button
            key={code}
            className={lang === code ? 'lang-btn lang-btn-active' : 'lang-btn'}
            onClick={() => setLang(code)}
          >
            {code.toUpperCase()}
          </button>
        ))}
      </div>

      <header className="dash-header">
        <div>
          <p className="dash-eyebrow">{t('reviewResponses')}</p>
          <h1>{businessName}</h1>
        </div>
        <button className="btn-refresh" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? t('checking') : t('checkNewReviews')}
        </button>
      </header>

      {reviews.length === 0 && (
        <div className="dash-state">{t('noReviewsYet')}</div>
      )}

      <div className="review-list">
        {reviews.map((r) => (
          <ReviewCard
            key={r.id}
            review={r}
            onEdit={handleDraftEdit}
            onSave={handleSaveDraft}
            onCopy={handleCopy}
            copied={copiedId === r.id}
            t={t}
          />
        ))}
      </div>
    </div>
  )
}

function ReviewCard({ review, onEdit, onSave, onCopy, copied, t }) {
  return (
    <div className="review-card">
      <div className="review-meta">
        <span className="stars" aria-label={`${review.rating} out of 5 stars`}>
          {'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}
        </span>
        <span className="review-author">{review.author_name}</span>
        <span className="review-time">{review.review_time}</span>
      </div>

      <p className="review-text">"{review.review_text}"</p>

      <div className="draft-block">
        <p className="draft-label">{t('draftedResponse')}</p>
        <textarea
          className="draft-textarea"
          value={review.drafted_response || ''}
          onChange={(e) => onEdit(review.id, e.target.value)}
          onBlur={(e) => onSave(review.id, e.target.value)}
          rows={3}
        />
        <button
          className="btn-copy"
          onClick={() => onCopy(review.id, review.drafted_response)}
        >
          {copied ? t('copied') : t('copyResponse')}
        </button>
      </div>
    </div>
  )
}

export default Dashboard
