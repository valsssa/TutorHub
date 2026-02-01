'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FiUser, FiCheck, FiAlertCircle } from 'react-icons/fi'
import { auth } from '@/lib/api'
import { User } from '@/types'
import { useToast } from '@/components/ToastContainer'
import Input from '@/components/Input'
import Button from '@/components/Button'

interface CompleteProfileProps {
  user: User
  onComplete: (updatedUser: User) => void
  redirectTo?: string
}

/**
 * Complete Profile Gate Component
 *
 * Blocks access until user provides required first_name and last_name.
 * Used for:
 * - OAuth users who signed up without providing names
 * - Legacy users migrated without complete profiles
 *
 * User Identity Contract:
 * - All registered users MUST have first_name and last_name
 * - This gate enforces completion before proceeding
 */
export default function CompleteProfile({ user, onComplete, redirectTo }: CompleteProfileProps) {
  const router = useRouter()
  const { showSuccess, showError } = useToast()
  const [firstName, setFirstName] = useState(user.first_name?.trim() || '')
  const [lastName, setLastName] = useState(user.last_name?.trim() || '')
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<{ firstName?: string; lastName?: string }>({})

  const validateForm = (): boolean => {
    const newErrors: { firstName?: string; lastName?: string } = {}

    const trimmedFirst = firstName.trim()
    const trimmedLast = lastName.trim()

    if (!trimmedFirst) {
      newErrors.firstName = 'First name is required'
    } else if (trimmedFirst.length > 100) {
      newErrors.firstName = 'First name must not exceed 100 characters'
    }

    if (!trimmedLast) {
      newErrors.lastName = 'Last name is required'
    } else if (trimmedLast.length > 100) {
      newErrors.lastName = 'Last name must not exceed 100 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setSaving(true)
    try {
      const updatedUser = await auth.updateUser({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      })

      showSuccess('Profile completed successfully!')
      onComplete(updatedUser)

      if (redirectTo) {
        router.push(redirectTo)
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail
      if (typeof detail === 'string') {
        showError(detail)
      } else if (Array.isArray(detail)) {
        showError(detail.map((d: any) => d.msg || d).join(', '))
      } else {
        showError('Failed to update profile. Please try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-xl">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FiUser className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Complete Your Profile
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Please provide your name to continue using EduConnect
            </p>
          </div>

          {/* Info Banner */}
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <FiAlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-amber-800 dark:text-amber-300 font-medium">
                  Why do we need your name?
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                  Your name helps tutors and students identify you and creates
                  a more personal learning experience.
                </p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="First Name"
              value={firstName}
              onChange={(e) => {
                setFirstName(e.target.value)
                if (errors.firstName) {
                  setErrors((prev) => ({ ...prev, firstName: undefined }))
                }
              }}
              placeholder="Enter your first name"
              error={errors.firstName}
              required
              autoComplete="given-name"
              autoFocus
            />

            <Input
              label="Last Name"
              value={lastName}
              onChange={(e) => {
                setLastName(e.target.value)
                if (errors.lastName) {
                  setErrors((prev) => ({ ...prev, lastName: undefined }))
                }
              }}
              placeholder="Enter your last name"
              error={errors.lastName}
              required
              autoComplete="family-name"
            />

            {/* Email Display (read-only) */}
            <div>
              <label className="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-1.5">
                Email
              </label>
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-600 dark:text-slate-400">
                {user.email}
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={saving}
              disabled={saving}
            >
              <FiCheck className="w-4 h-4" />
              Complete Profile
            </Button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-slate-500 dark:text-slate-400 mt-6">
            By completing your profile, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  )
}
