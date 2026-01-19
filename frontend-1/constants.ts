
import { Tutor, Session, User, UserRole, VerificationRequest, ChatThread } from './types';

export const SUBJECTS = ['All', 'Mathematics', 'Physics', 'Computer Science', 'English Literature', 'Chemistry', 'History'];
export const COUNTRIES = ['Any country', 'United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'France'];
export const AVAILABILITY_OPTIONS = ['Any time', 'Weekdays', 'Weekends', 'Mornings (8-12)', 'Afternoons (12-5)', 'Evenings (5-9)'];
export const SORT_OPTIONS = ['Our top picks', 'Price: Low to High', 'Price: High to Low', 'Highest Rated', 'Most Popular'];

export const MOCK_TUTORS: Tutor[] = [
  {
    id: 't1',
    name: 'Dr. Elena Vance',
    title: 'PhD in Astrophysics',
    subject: 'Physics',
    rating: 4.9,
    reviews: 124,
    hourlyRate: 85,
    isVerified: true,
    imageUrl: 'https://picsum.photos/seed/elena/200/200',
    bio: 'Former researcher at CERN, specializing in making complex physics concepts accessible to high school and college students.',
    topics: ['Mechanics', 'Quantum Physics', 'Calculus'],
    availability: ['2024-06-20T10:00:00', '2024-06-20T14:00:00', '2024-06-21T09:00:00'],
    education: ['PhD Astrophysics, MIT', 'BS Physics, Stanford University'],
    philosophy: 'I believe that physics is not just about equations, but about understanding the fundamental nature of reality. My goal is to help you see the world through the lens of a physicist.',
    reviewsList: [
      { id: 'r1', studentName: 'Sarah K.', rating: 5, comment: 'Dr. Vance is incredible! She explained quantum mechanics in a way that finally made sense.', date: '2024-05-10' },
      { id: 'r2', studentName: 'Mike T.', rating: 5, comment: 'Very patient and knowledgeable. Highly recommend.', date: '2024-05-02' }
    ],
    nativeLanguage: 'English',
    languages: ['English', 'French', 'German']
  },
  {
    id: 't2',
    name: 'James Chen',
    title: 'Senior Software Engineer',
    subject: 'Computer Science',
    rating: 4.8,
    reviews: 89,
    hourlyRate: 60,
    isVerified: true,
    imageUrl: 'https://picsum.photos/seed/james/200/200',
    bio: 'Full-stack developer with 10 years of experience. I teach React, Node.js, and Python with a focus on practical projects.',
    topics: ['React', 'TypeScript', 'Algorithms'],
    availability: ['2024-06-20T16:00:00', '2024-06-22T10:00:00'],
    education: ['MS Computer Science, UC Berkeley', 'BS Computer Science, University of Washington'],
    philosophy: 'Learn by doing. We will build real applications together, not just memorize syntax.',
    reviewsList: [
      { id: 'r3', studentName: 'Alex J.', rating: 4, comment: 'Great practical examples. Sometimes goes a bit fast, but very helpful.', date: '2024-06-01' }
    ],
    nativeLanguage: 'English',
    languages: ['English', 'Chinese (Mandarin)']
  },
  {
    id: 't3',
    name: 'Sarah Miller',
    title: 'Certified Math Instructor',
    subject: 'Mathematics',
    rating: 4.7,
    reviews: 210,
    hourlyRate: 45,
    isVerified: false, 
    imageUrl: 'https://picsum.photos/seed/sarah/200/200',
    bio: 'Passionate about Algebra and Geometry. I help students overcome math anxiety and build strong foundational skills.',
    topics: ['Algebra', 'Geometry', 'Trigonometry'],
    availability: ['2024-06-20T11:00:00', '2024-06-21T13:00:00'],
    education: ['M.Ed. Mathematics Education, Boston College', 'BS Mathematics, Boston University'],
    philosophy: 'Math is for everyone. My approach focuses on building confidence through small wins and clear, step-by-step logic.',
    reviewsList: [
      { id: 'r4', studentName: 'Emily R.', rating: 5, comment: 'Sarah saved my grade! I used to hate math, now I tolerate it :)', date: '2024-05-20' }
    ],
    nativeLanguage: 'English',
    languages: ['English', 'Spanish']
  },
  {
    id: 't4',
    name: 'Marcus Thorne',
    title: 'Literature Professor',
    subject: 'English Literature',
    rating: 5.0,
    reviews: 56,
    hourlyRate: 70,
    isVerified: true,
    imageUrl: 'https://picsum.photos/seed/marcus/200/200',
    bio: `Expert in Shakespearean studies and modern American literature. Improve your essay writing and critical analysis.

I have over 15 years of experience teaching at the university level, specializing in the works of William Shakespeare and contemporary American novelists. My passion lies in helping students unlock the deeper meanings within texts, fostering a love for literature that goes beyond the classroom.

My teaching methodology is rooted in the belief that literature is a conversation. Whether we are dissecting the soliloquies of Hamlet or analyzing the symbolism in The Great Gatsby, I encourage open dialogue and critical thinking. I have guided hundreds of students through the rigorous process of academic essay writing, helping them refine their arguments, structure their thoughts, and polish their prose. My goal is not just to help you get a better grade, but to help you become a more articulate and confident writer.

I hold a PhD in English Literature from Oxford University, where my research focused on the intersection of performance and text in early modern drama. Before that, I completed my BA at Yale. I have published several papers in academic journals and am currently working on a book about the evolution of the tragic hero.

In our lessons, we can focus on specific texts you are studying in school, work on improving your general writing skills, or prepare for standardized tests like the AP English Literature exam. I tailor my approach to each student's unique learning style and goals. Let's embark on this literary journey together and discover the power of words.`,
    topics: ['Essay Writing', 'Shakespeare', 'Creative Writing'],
    availability: ['2024-06-21T15:00:00'],
    education: ['PhD English Literature, Oxford University', 'BA English, Yale University'],
    philosophy: 'Literature is a conversation across centuries. I help students join that conversation with clarity and insight.',
    reviewsList: [
      { id: 'r5', studentName: 'Jessica L.', rating: 5, comment: 'Absolutely brilliant. Marcus helped me craft the perfect college essay.', date: '2024-04-15' }
    ],
    nativeLanguage: 'English',
    languages: ['English', 'Latin']
  },
  {
    id: 'new_t1',
    name: 'Alice Walker',
    title: 'Chemistry Enthusiast',
    subject: 'Chemistry',
    rating: 0,
    reviews: 0,
    hourlyRate: 40,
    isVerified: false,
    imageUrl: 'https://picsum.photos/seed/alice/200/200',
    bio: 'Recent graduate passionate about teaching Chemistry concepts to high school students through interactive experiments.',
    topics: ['Organic Chemistry', 'Lab Safety', 'Stoichiometry'],
    availability: ['2024-06-26T10:00:00'],
    education: ['PhD Chemistry, UCLA', 'BS Chemistry, UC San Diego'],
    philosophy: 'Chemistry is life. Understanding the molecular world unlocks a deeper appreciation for everything around us.',
    reviewsList: [],
    nativeLanguage: 'English',
    languages: ['English']
  },
  {
    id: 'new_t2',
    name: 'David Kim',
    title: 'Math Tutor',
    subject: 'Mathematics',
    rating: 0,
    reviews: 0,
    hourlyRate: 35,
    isVerified: false, 
    imageUrl: 'https://picsum.photos/seed/david/200/200',
    bio: 'Helping students master math basics and prepare for standardized tests with proven strategies.',
    topics: ['Calculus', 'Algebra', 'SAT Math'],
    availability: ['2024-06-27T14:00:00'],
    education: ['MS Mathematics, UT Austin'],
    philosophy: 'Math is a language. Once you learn the grammar, you can express anything.',
    reviewsList: [],
    nativeLanguage: 'English',
    languages: ['English', 'Korean']
  }
];

export const MOCK_STUDENT: User = {
  id: 's1',
  name: 'Alex Johnson',
  role: UserRole.STUDENT,
  avatarUrl: 'https://picsum.photos/seed/alex/100/100',
  balance: 150,
  savedTutorIds: ['t1']
};

export const MOCK_TUTOR_USER: User = {
  id: 't1', 
  name: 'Dr. Elena Vance',
  role: UserRole.TUTOR,
  avatarUrl: 'https://picsum.photos/seed/elena/100/100',
  earnings: 3450
};

export const MOCK_ADMIN: User = {
  id: 'a1',
  name: 'System Admin',
  role: UserRole.ADMIN,
  avatarUrl: 'https://picsum.photos/seed/admin/100/100'
};

export const MOCK_OWNER: User = {
  id: 'o1',
  name: 'Platform Owner',
  role: UserRole.OWNER,
  avatarUrl: 'https://ui-avatars.com/api/?name=Owner&background=000&color=fff'
};

export const MOCK_SESSIONS: Session[] = [
  {
    id: 'ses1',
    tutorId: 't2',
    tutorName: 'James Chen',
    studentId: 's1',
    date: '2024-06-20T16:00:00',
    status: 'upcoming',
    price: 60,
    subject: 'Computer Science'
  },
  {
    id: 'ses2',
    tutorId: 't3',
    tutorName: 'Sarah Miller',
    studentId: 's1',
    date: '2024-06-15T11:00:00',
    status: 'completed',
    price: 45,
    subject: 'Mathematics',
    isReviewed: false
  }
];

export const MOCK_VERIFICATION_REQUESTS: VerificationRequest[] = [
  {
    id: 'vr1',
    tutorId: 'new_t1',
    tutorName: 'Alice Walker',
    email: 'alice@example.com',
    subject: 'Chemistry',
    submittedDate: '2024-06-25',
    status: 'pending',
    documents: [
      { name: 'PhD_Chemistry.pdf', type: 'application/pdf', url: '#' },
      { name: 'Teaching_Cert.pdf', type: 'application/pdf', url: '#' }
    ]
  },
  {
    id: 'vr2',
    tutorId: 'new_t2',
    tutorName: 'David Kim',
    email: 'david.k@example.com',
    subject: 'Mathematics',
    submittedDate: '2024-06-24',
    status: 'pending',
    documents: [
      { name: 'Masters_Math.jpg', type: 'image/jpeg', url: '#' }
    ]
  }
];

export const MOCK_CHATS: ChatThread[] = [
  {
    id: 'chat1',
    participantId: 't2',
    participantName: 'James Chen',
    participantAvatar: 'https://picsum.photos/seed/james/200/200',
    lastMessage: 'Sure, we can focus on React Hooks next session.',
    lastUpdated: '2024-06-19T10:30:00',
    unreadCount: 1,
    messages: [
      { id: 'm1', senderId: 's1', text: 'Hi James, quick question about the homework.', timestamp: '2024-06-19T10:00:00' },
      { id: 'm2', senderId: 't2', text: 'Sure, we can focus on React Hooks next session.', timestamp: '2024-06-19T10:30:00' }
    ]
  },
  {
    id: 'chat2',
    participantId: 't3',
    participantName: 'Sarah Miller',
    participantAvatar: 'https://picsum.photos/seed/sarah/200/200',
    lastMessage: 'Thanks for the great review!',
    lastUpdated: '2024-06-15T14:00:00',
    unreadCount: 0,
    messages: [
      { id: 'm1', senderId: 't3', text: 'Thanks for the great review!', timestamp: '2024-06-15T14:00:00' }
    ]
  }
];
