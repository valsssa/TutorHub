import confetti from 'canvas-confetti'

interface ConfettiOptions {
  particleCount?: number;
  spread?: number;
  startVelocity?: number;
  decay?: number;
  scalar?: number;
  origin?: { x?: number; y?: number };
  colors?: string[];
  ticks?: number;
  zIndex?: number;
}

export const triggerConfetti = () => {
  const count = 200
  const defaults = {
    origin: { y: 0.7 }
  }

  function fire(particleRatio: number, opts: ConfettiOptions) {
    confetti({
      ...defaults,
      ...opts,
      particleCount: Math.floor(count * particleRatio)
    })
  }

  fire(0.25, {
    spread: 26,
    startVelocity: 55,
  })

  fire(0.2, {
    spread: 60,
  })

  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8
  })

  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2
  })

  fire(0.1, {
    spread: 120,
    startVelocity: 45,
  })
}

export const triggerSuccessConfetti = () => {
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#F43F5E', '#FBBF24', '#38BDF8', '#10B981']
  })
}

export const triggerMilestoneConfetti = () => {
  const duration = 3 * 1000
  const animationEnd = Date.now() + duration
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 100 }

  function randomInRange(min: number, max: number) {
    return Math.random() * (max - min) + min
  }

  const interval: ReturnType<typeof setInterval> = setInterval(function() {
    const timeLeft = animationEnd - Date.now()

    if (timeLeft <= 0) {
      return clearInterval(interval)
    }

    const particleCount = 50 * (timeLeft / duration)
    
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
    })
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
    })
  }, 250)
}
