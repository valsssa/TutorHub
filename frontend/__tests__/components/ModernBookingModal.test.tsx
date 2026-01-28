import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ModernBookingModal } from '@/components/ModernBookingModal'

jest.mock('@/lib/api', () => ({
  tutors: {
    getAvailability: jest.fn(),
    createBooking: jest.fn()
  },
  subjects: {
    list: jest.fn()
  }
}))

describe('ModernBookingModal', () => {
  const mockTutor = {
    id: 1,
    name: 'Alice Johnson',
    hourly_rate: 50
  }

  const mockOnClose = jest.fn()
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders booking modal with tutor info', () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Then
    expect(screen.getByText('Book Session with Alice Johnson')).toBeInTheDocument()
    expect(screen.getByText('$50.00/hour')).toBeInTheDocument()
  })

  it('displays subject selection dropdown', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, name: 'Mathematics' },
        { id: 2, name: 'English' }
      ]
    })

    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Then
    expect(screen.getByLabelText('Subject')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
      expect(screen.getByText('English')).toBeInTheDocument()
    })
  })

  it('displays date and time picker', () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Then
    expect(screen.getByLabelText(/Date/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Time/i)).toBeInTheDocument()
  })

  it('calculates total price based on duration', async () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Select 2 hour duration (120 minutes)
    const durationSelect = screen.getByLabelText('Duration')
    fireEvent.change(durationSelect, { target: { value: '120' } })

    // Then
    await waitFor(() => {
      expect(screen.getByText('$100.00')).toBeInTheDocument() // 50 * 2
      expect(screen.getByText('Total: $100.00')).toBeInTheDocument()
    })
  })

  it('shows validation error for past date', async () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    const dateInput = screen.getByLabelText(/Date/i)
    const pastDate = '2020-01-01'
    fireEvent.change(dateInput, { target: { value: pastDate } })

    const submitButton = screen.getByText('Book Session')
    fireEvent.click(submitButton)

    // Then
    await waitFor(() => {
      expect(screen.getByText(/Date must be in the future/i)).toBeInTheDocument()
    })
  })

  it('validates required fields', async () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Try to submit without filling required fields
    const submitButton = screen.getByText('Book Session')
    fireEvent.click(submitButton)

    // Then
    await waitFor(() => {
      expect(screen.getByText(/Subject is required/i)).toBeInTheDocument()
      expect(screen.getByText(/Date is required/i)).toBeInTheDocument()
      expect(screen.getByText(/Time is required/i)).toBeInTheDocument()
    })
  })

  it('submits booking data on form submit', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [{ id: 1, name: 'Mathematics' }]
    })

    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Fill form
    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText(/Date/i), { target: { value: '2025-02-01' } })
    fireEvent.change(screen.getByLabelText(/Time/i), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('Duration'), { target: { value: '60' } })
    fireEvent.change(screen.getByLabelText('Notes'), { target: { value: 'Looking forward to learning!' } })

    // Submit
    fireEvent.click(screen.getByText('Book Session'))

    // Then
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        subject_id: 1,
        start_at: expect.any(String),
        duration_minutes: 60,
        notes_student: 'Looking forward to learning!'
      })
    })
  })

  it('closes modal when cancel button clicked', () => {
    // Given
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // When
    fireEvent.click(screen.getByText('Cancel'))

    // Then
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('loads and displays available time slots', async () => {
    // Given
    const { tutors } = await import('@/lib/api')
    ;(tutors.getAvailability as jest.Mock).mockResolvedValue({
      data: [
        { start_time: '09:00', end_time: '10:00' },
        { start_time: '10:00', end_time: '11:00' },
        { start_time: '14:00', end_time: '15:00' }
      ]
    })

    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Select date to trigger availability loading
    fireEvent.change(screen.getByLabelText(/Date/i), { target: { value: '2025-02-01' } })

    // Then
    await waitFor(() => {
      expect(screen.getByText('9:00 AM')).toBeInTheDocument()
      expect(screen.getByText('10:00 AM')).toBeInTheDocument()
      expect(screen.getByText('2:00 PM')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    // Given
    mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Submit form
    fireEvent.click(screen.getByText('Book Session'))

    // Then
    expect(screen.getByText('Booking...')).toBeInTheDocument()
    expect(screen.getByText('Book Session')).toBeDisabled()
  })

  it('displays error message on submission failure', async () => {
    // Given
    mockOnSubmit.mockRejectedValue(new Error('Booking conflict'))

    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Submit form
    fireEvent.click(screen.getByText('Book Session'))

    // Then
    await waitFor(() => {
      expect(screen.getByText('Booking conflict')).toBeInTheDocument()
    })
  })

  it('resets form when reopened', () => {
    // Given - First render
    const { rerender } = render(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Fill some data
    fireEvent.change(screen.getByLabelText('Notes'), { target: { value: 'Test notes' } })

    // Close and reopen
    rerender(
      <ModernBookingModal
        isOpen={false}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    rerender(
      <ModernBookingModal
        isOpen={true}
        tutor={mockTutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Then - Form should be reset
    expect(screen.getByLabelText('Notes')).toHaveValue('')
  })
})