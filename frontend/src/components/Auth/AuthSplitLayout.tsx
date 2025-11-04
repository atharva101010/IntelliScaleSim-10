import React from 'react'
import { Link } from 'react-router-dom'
import { FaFacebookF, FaGoogle, FaTwitter } from 'react-icons/fa'

type Props = {
  // Which side holds the form
  formSide?: 'left' | 'right'
  // Accent color for the message panel
  tone?: 'rose' | 'teal'
  // Message (colored) panel
  messageTitle: string
  messageSubtitle?: string
  messageCtaText: string
  messageCtaTo: string
  // Form panel
  formTitle: string
  children: React.ReactNode
  showSocialIcons?: boolean
}

/**
 * Split 2-column auth layout (white form panel + colored message panel),
 * configurable for which side the form sits on to match different mockups.
 */
const AuthSplitLayout: React.FC<Props> = ({
  formSide = 'left',
  tone = 'rose',
  messageTitle,
  messageSubtitle,
  messageCtaText,
  messageCtaTo,
  formTitle,
  children,
  showSocialIcons = false,
}) => {
  const toneBg = tone === 'rose' ? 'bg-rose-500' : 'bg-teal-600'

  const MessagePanel = (
    <div className={`p-8 sm:p-10 lg:p-12 ${toneBg} text-white flex items-center justify-center`}> 
      <div className="text-center max-w-sm">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{messageTitle}</h2>
        {messageSubtitle && (
          <p className="mt-2 text-white/90 text-sm">{messageSubtitle}</p>
        )}
        <Link
          to={messageCtaTo}
          className="mt-6 inline-flex items-center justify-center rounded-full border-2 border-white/90 px-6 py-2 font-semibold hover:bg-white/10"
        >
          {messageCtaText}
        </Link>
      </div>
    </div>
  )

  const FormPanel = (
    <div className="p-8 sm:p-10 lg:p-12 bg-white">
      <div className="max-w-md">
        <div className="flex items-center justify-between">
          <h3 className="text-2xl font-semibold tracking-tight">{formTitle}</h3>
          {showSocialIcons && (
            <div className="flex items-center gap-2 text-slate-500">
              <a href="#" aria-label="Continue with Facebook" className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 hover:bg-slate-50">
                <FaFacebookF size={12} />
              </a>
              <a href="#" aria-label="Continue with Google" className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 hover:bg-slate-50">
                <FaGoogle size={12} />
              </a>
              <a href="#" aria-label="Continue with Twitter" className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 hover:bg-slate-50">
                <FaTwitter size={12} />
              </a>
            </div>
          )}
        </div>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )

  return (
    <div className="relative">
      {/* soft background accents matching tone */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        {tone === 'rose' ? (
          <>
            <div className="absolute -top-10 -right-10 h-56 w-56 rounded-full bg-rose-200/50 blur-2xl" />
            <div className="absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-orange-200/40 blur-2xl" />
          </>
        ) : (
          <>
            <div className="absolute -top-10 -right-10 h-56 w-56 rounded-full bg-teal-200/50 blur-2xl" />
            <div className="absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-emerald-200/40 blur-2xl" />
          </>
        )}
      </div>
      <div className="grid place-items-center">
        <div className="w-full max-w-5xl">
          <div className="grid grid-cols-1 lg:grid-cols-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          {formSide === 'left' ? (
            <>
              {FormPanel}
              {MessagePanel}
            </>
          ) : (
            <>
              {MessagePanel}
              {FormPanel}
            </>
          )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthSplitLayout
