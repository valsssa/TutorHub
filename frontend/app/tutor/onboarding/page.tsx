"use client";

import Image from "next/image";
import React, { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FiCheck, FiAlertCircle, FiUpload, FiCamera, FiPlus, FiX, FiStar } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import StepIndicator from "@/components/StepIndicator";
import Button from "@/components/Button";
import Input from "@/components/Input";
import TextArea from "@/components/TextArea";
import { useToast } from "@/components/ToastContainer";
import { tutors, subjects as subjectsApi } from "@/lib/api";
import type { Subject } from "@/types";

// CEFR Language Proficiency Levels (matching backend validation)
const LANGUAGE_LEVELS = [
  { value: 'Native', label: 'Native' },
  { value: 'C2', label: 'C2 - Proficient' },
  { value: 'C1', label: 'C1 - Advanced' },
  { value: 'B2', label: 'B2 - Upper Intermediate' },
  { value: 'B1', label: 'B1 - Intermediate' },
  { value: 'A2', label: 'A2 - Elementary' },
  { value: 'A1', label: 'A1 - Beginner' },
];

const COUNTRIES = [
  'Albania', 'United States', 'United Kingdom', 'Canada', 'Australia',
  'Germany', 'France', 'Spain', 'Italy', 'Japan', 'China', 'India',
  'Brazil', 'Mexico', 'Argentina', 'Netherlands', 'Sweden', 'Norway'
];

type LanguageOption = {
  value: string;
  label: string;
};

const LANGUAGES_LIST: LanguageOption[] = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ru', label: 'Russian' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'ar', label: 'Arabic' },
  { value: 'hi', label: 'Hindi' },
  { value: 'sq', label: 'Albanian' },
  { value: 'am', label: 'Amharic' },
  { value: 'sw', label: 'Swahili' },
  { value: 'nl', label: 'Dutch' },
  { value: 'pl', label: 'Polish' },
  { value: 'tr', label: 'Turkish' },
  { value: 'el', label: 'Greek' },
  { value: 'sv', label: 'Swedish' },
  { value: 'no', label: 'Norwegian' },
];

const DEGREE_TYPES = [
  "Bachelor&apos;s Degree",
  "Master&apos;s Degree",
  "PhD",
  "Associate Degree",
  "Diploma",
  "Certificate"
];

type LanguageEntry = {
  language: string;
  level: string;
};

type CertificationEntry = {
  subject: string;
  name: string;
  yearsFrom: string;
  yearsTo: string;
  file: File | null;
};

type EducationEntry = {
  university: string;
  degree: string;
  degreeType: string;
  specialization: string;
  yearsFrom: string;
  yearsTo: string;
  file: File | null;
};

type OnboardingData = {
  // Step 1: Personal Info
  firstName: string;
  lastName: string;
  email: string;
  countryOfBirth: string;
  subject: string;
  languages: LanguageEntry[];
  phoneNumber: string;
  phoneCountryCode: string;
  over18: boolean;

  // Step 2: Profile Photo
  profilePhoto: File | null;

  // Step 3: Teaching Certification
  hasCertificate: boolean;
  certificates: CertificationEntry[];

  // Step 4: Education
  hasHigherEducation: boolean;
  education: EducationEntry[];

  // Step 5: Description
  description: string;
};

export default function TutorOnboardingPage() {
  return (
    <ProtectedRoute requiredRole="tutor">
      <TutorOnboardingContent />
    </ProtectedRoute>
  );
}

function TutorOnboardingContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState<OnboardingData>({
    firstName: '',
    lastName: '',
    email: '',
    countryOfBirth: '',
    subject: '',
    languages: [{ language: '', level: '' }],
    phoneNumber: '',
    phoneCountryCode: '+1',
    over18: false,
    profilePhoto: null,
    hasCertificate: false,
    certificates: [],
    hasHigherEducation: false,
    education: [],
    description: '',
  });

  const STEP_TITLES = [
    'About You',
    'Profile Photo',
    'Certifications',
    'Education',
    'Description',
  ];

  const loadSubjects = useCallback(async () => {
    try {
      const data = await subjectsApi.list();
      setSubjectsList(data);
    } catch (error) {
      showError("Failed to load subjects");
    }
  }, [showError]);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    return () => {
      if (photoPreview) {
        URL.revokeObjectURL(photoPreview);
      }
    };
  }, [photoPreview]);

  const updateFormData = (field: keyof OnboardingData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePhotoChange = (file: File | null) => {
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }

    updateFormData('profilePhoto', file);

    if (file) {
      const preview = URL.createObjectURL(file);
      setPhotoPreview(preview);
    } else {
      setPhotoPreview(null);
    }
  };

  const addLanguage = () => {
    updateFormData('languages', [...formData.languages, { language: '', level: '' }]);
  };

  const removeLanguage = (index: number) => {
    if (formData.languages.length > 1) {
      updateFormData(
        'languages',
        formData.languages.filter((_, i) => i !== index)
      );
    }
  };

  const updateLanguage = (index: number, field: keyof LanguageEntry, value: string) => {
    const updated = formData.languages.map((lang, i) =>
      i === index ? { ...lang, [field]: value } : lang
    );
    updateFormData('languages', updated);
  };

  const addCertificate = () => {
    updateFormData('certificates', [
      ...formData.certificates,
      { subject: '', name: '', yearsFrom: '', yearsTo: '', file: null },
    ]);
  };

  const removeCertificate = (index: number) => {
    updateFormData(
      'certificates',
      formData.certificates.filter((_, i) => i !== index)
    );
  };

  const updateCertificate = (
    index: number,
    field: keyof CertificationEntry,
    value: any
  ) => {
    const updated = formData.certificates.map((cert, i) =>
      i === index ? { ...cert, [field]: value } : cert
    );
    updateFormData('certificates', updated);
  };

  const addEducation = () => {
    updateFormData('education', [
      ...formData.education,
      {
        university: '',
        degree: '',
        degreeType: '',
        specialization: '',
        yearsFrom: '',
        yearsTo: '',
        file: null,
      },
    ]);
  };

  const removeEducation = (index: number) => {
    updateFormData(
      'education',
      formData.education.filter((_, i) => i !== index)
    );
  };

  const updateEducation = (
    index: number,
    field: keyof EducationEntry,
    value: any
  ) => {
    const updated = formData.education.map((edu, i) =>
      i === index ? { ...edu, [field]: value } : edu
    );
    updateFormData('education', updated);
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!formData.firstName.trim()) newErrors.firstName = 'First name is required';
        if (!formData.lastName.trim()) newErrors.lastName = 'Last name is required';
        if (!formData.email.trim()) newErrors.email = 'Email is required';
        if (!formData.countryOfBirth) newErrors.countryOfBirth = 'Country of birth is required';
        if (!formData.subject) newErrors.subject = 'Subject is required';
        if (!formData.languages[0]?.language) newErrors.languages = 'At least one language is required';
        if (!formData.over18) newErrors.over18 = 'You must confirm you are over 18';
        break;
      case 2:
        if (!formData.profilePhoto) newErrors.profilePhoto = 'Profile photo is required';
        break;
      case 5:
        if (formData.description.length < 400) {
          newErrors.description = 'Description must be at least 400 characters';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 5));
      setErrors({});
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
    setErrors({});
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) {
      return;
    }

    setSubmitting(true);
    try {
      // Step 1: Create basic profile
      const profilePayload = {
        title: `${formData.subject} Tutor`,
        headline: `${formData.firstName} ${formData.lastName} - ${formData.subject} Expert`,
        bio: formData.description.substring(0, 500),
        experience_years: 1,
        languages: formData.languages
          .filter((l) => l.language)
          .map((l) => l.language),
      };

      await tutors.updateAbout(profilePayload);

      // Step 2: Upload photo
      if (formData.profilePhoto) {
        await tutors.updateProfilePhoto(formData.profilePhoto);
      }

      // Step 3: Upload certifications
      if (!formData.hasCertificate && formData.certificates.length > 0) {
        const files: Record<number, File> = {};
        const certificationsPayload = formData.certificates
          .filter((cert) => cert.name.trim())
          .map((cert, idx) => {
            if (cert.file) {
              files[idx] = cert.file;
            }
            return {
              name: cert.name.trim(),
              issuing_organization: cert.subject || undefined,
              issue_date: cert.yearsFrom ? `${cert.yearsFrom}-01-01` : undefined,
              expiration_date: cert.yearsTo ? `${cert.yearsTo}-12-31` : undefined,
            };
          });

        if (certificationsPayload.length > 0) {
          await tutors.replaceCertifications({
            certifications: certificationsPayload,
            files: Object.keys(files).length ? files : undefined,
          });
        }
      }

      // Step 4: Upload education
      if (!formData.hasHigherEducation && formData.education.length > 0) {
        const files: Record<number, File> = {};
        const educationPayload = formData.education
          .filter((edu) => edu.university.trim())
          .map((edu, idx) => {
            if (edu.file) {
              files[idx] = edu.file;
            }
            return {
              institution: edu.university.trim(),
              degree: edu.degree?.trim() || undefined,
              field_of_study: edu.specialization?.trim() || undefined,
              start_year: edu.yearsFrom ? Number(edu.yearsFrom) : undefined,
              end_year: edu.yearsTo ? Number(edu.yearsTo) : undefined,
            };
          });

        if (educationPayload.length > 0) {
          await tutors.replaceEducation({
            education: educationPayload,
            files: Object.keys(files).length ? files : undefined,
          });
        }
      }

      // Step 5: Update full description
      await tutors.updateDescription({ description: formData.description.trim() });

      // Step 6: Submit profile for review
      await tutors.submitForReview();

      showSuccess('Profile submitted for review!');
      setTimeout(() => {
        router.push('/tutor/profile/submitted');
      }, 1500);
    } catch (error) {
      const err = error as { response?: { data?: { detail?: unknown } }; message?: string };
      const detail = err.response?.data?.detail;

      let message = 'Failed to create profile';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        const extracted = detail
          .map((item) => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object') {
              const candidate = item as Record<string, unknown>;
              if (typeof candidate.msg === 'string') return candidate.msg;
              if (typeof candidate.detail === 'string') return candidate.detail;
            }
            return null;
          })
          .filter((value): value is string => Boolean(value));
        if (extracted.length > 0) {
          message = extracted.join('; ');
        }
      } else if (detail && typeof detail === 'object') {
        const candidate = detail as Record<string, unknown>;
        if (typeof candidate.msg === 'string') {
          message = candidate.msg;
        } else if (typeof candidate.detail === 'string') {
          message = candidate.detail;
        }
      } else if (err.message) {
        message = err.message;
      }

      showError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">About You</h2>
        <p className="text-gray-600">
          Start creating your public tutor profile. Your progress will be automatically saved as you
          complete each section.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input
          label="First name *"
          value={formData.firstName}
          onChange={(e) => updateFormData('firstName', e.target.value)}
          placeholder="John"
          error={errors.firstName}
          required
        />
        <Input
          label="Last name *"
          value={formData.lastName}
          onChange={(e) => updateFormData('lastName', e.target.value)}
          placeholder="Doe"
          error={errors.lastName}
          required
        />
        <Input
          label="Email *"
          type="email"
          value={formData.email}
          onChange={(e) => updateFormData('email', e.target.value)}
          placeholder="john.doe@email.com"
          error={errors.email}
          required
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Country of birth *
          </label>
          <select
            value={formData.countryOfBirth}
            onChange={(e) => updateFormData('countryOfBirth', e.target.value)}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500
              ${errors.countryOfBirth ? 'border-red-500' : 'border-gray-300'}
            `}
          >
            <option value="">Select country</option>
            {COUNTRIES.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
          {errors.countryOfBirth && (
            <p className="text-red-500 text-sm mt-1">{errors.countryOfBirth}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subject you teach *
          </label>
          <select
            value={formData.subject}
            onChange={(e) => updateFormData('subject', e.target.value)}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500
              ${errors.subject ? 'border-red-500' : 'border-gray-300'}
            `}
          >
            <option value="">Select subject</option>
            {subjectsList.map((subject) => (
              <option key={subject.id} value={subject.name}>
                {subject.name}
              </option>
            ))}
          </select>
          {errors.subject && <p className="text-red-500 text-sm mt-1">{errors.subject}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone number (optional)
          </label>
          <div className="flex gap-2">
            <select
              value={formData.phoneCountryCode}
              onChange={(e) => updateFormData('phoneCountryCode', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="+1">+1</option>
              <option value="+44">+44</option>
              <option value="+355">+355</option>
              <option value="+49">+49</option>
              <option value="+33">+33</option>
            </select>
            <input
              type="tel"
              value={formData.phoneNumber}
              onChange={(e) => updateFormData('phoneNumber', e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="123-456-7890"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">Languages you speak *</label>
        {formData.languages.map((lang, index) => (
          <div key={index} className="flex gap-3 items-start">
            <select
              value={lang.language}
              onChange={(e) => updateLanguage(index, 'language', e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select language</option>
              {LANGUAGES_LIST.map((language) => (
                <option key={language.value} value={language.value}>
                  {language.label}
                </option>
              ))}
            </select>
            <select
              value={lang.level}
              onChange={(e) => updateLanguage(index, 'level', e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Level</option>
              {LANGUAGE_LEVELS.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
            {formData.languages.length > 1 && (
              <button
                type="button"
                onClick={() => removeLanguage(index)}
                className="mt-1 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              >
                <FiX className="w-5 h-5" />
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addLanguage}
          className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
        >
          <FiPlus className="w-4 h-4" />
          Add another language
        </button>
        {errors.languages && <p className="text-red-500 text-sm">{errors.languages}</p>}
      </div>

      <div className="flex items-center gap-3 pt-4">
        <input
          type="checkbox"
          checked={formData.over18}
          onChange={(e) => updateFormData('over18', e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label className="text-sm text-gray-700">I confirm I&apos;m over 18 *</label>
      </div>
      {errors.over18 && <p className="text-red-500 text-sm">{errors.over18}</p>}
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Photo</h2>
        <p className="text-gray-600">
          Choose a photo that will help learners get to know you.
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">What your photo needs</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          {[
            'You should be facing forward',
            'Frame your head and shoulders',
            'You should be centered and upright',
            'Your face and eyes should be visible (except for religious reasons)',
            'You should be the only person in the photo',
            'Use a color photo with high resolution and no filters',
          ].map((requirement, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <FiCheck className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {requirement}
            </li>
          ))}
          <li className="flex items-start gap-2">
            <FiX className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" />
            Avoid logos or contact information
          </li>
        </ul>
      </div>

      <div className="flex flex-col items-center">
        <div className="relative">
          {photoPreview ? (
            <Image
              src={photoPreview}
              alt="Profile preview"
              width={128}
              height={128}
              className="w-32 h-32 rounded-full object-cover border-4 border-blue-200"
              unoptimized
            />
          ) : (
            <div className="w-32 h-32 bg-gray-200 rounded-full flex items-center justify-center border-2 border-dashed border-gray-400">
              <FiCamera className="w-8 h-8 text-gray-500" />
            </div>
          )}
          <label className="absolute bottom-0 right-0 bg-primary-600 text-white p-2 rounded-full cursor-pointer hover:bg-primary-700 transition-colors">
            <FiUpload className="w-4 h-4" />
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handlePhotoChange(e.target.files?.[0] || null)}
              className="hidden"
            />
          </label>
        </div>
        {errors.profilePhoto && (
          <p className="text-red-500 text-sm mt-2">{errors.profilePhoto}</p>
        )}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Teaching Certification</h2>
        <p className="text-gray-600">
          Do you have teaching certificates? If so, describe them to enhance your profile
          credibility and get more students.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={formData.hasCertificate}
          onChange={(e) => updateFormData('hasCertificate', e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label className="text-sm text-gray-700">I don&apos;t have a teaching certificate</label>
      </div>

      {!formData.hasCertificate && (
        <div className="space-y-4">
          {formData.certificates.map((cert, index) => (
            <div key={index} className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
                  <select
                    value={cert.subject}
                    onChange={(e) => updateCertificate(index, 'subject', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select subject</option>
                    {subjectsList.map((subject) => (
                      <option key={subject.id} value={subject.name}>
                        {subject.name}
                      </option>
                    ))}
                  </select>
                </div>
                <Input
                  label="Certification"
                  value={cert.name}
                  onChange={(e) => updateCertificate(index, 'name', e.target.value)}
                  placeholder="Write the name exactly as it appears on your certificate"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Year from"
                  type="number"
                  value={cert.yearsFrom}
                  onChange={(e) => updateCertificate(index, 'yearsFrom', e.target.value)}
                  placeholder="2020"
                  min="1950"
                  max={new Date().getFullYear().toString()}
                />
                <Input
                  label="Year to"
                  type="number"
                  value={cert.yearsTo}
                  onChange={(e) => updateCertificate(index, 'yearsTo', e.target.value)}
                  placeholder="2023"
                  min="1950"
                  max={new Date().getFullYear().toString()}
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload certificate
                  </label>
                  <label className="w-full px-4 py-2 border border-gray-300 rounded-lg text-center text-gray-600 hover:bg-gray-50 cursor-pointer flex items-center justify-center gap-2">
                    <FiUpload className="w-4 h-4" />
                    {cert.file ? cert.file.name : 'Choose file'}
                    <input
                      type="file"
                      onChange={(e) =>
                        updateCertificate(index, 'file', e.target.files?.[0] || null)
                      }
                      className="hidden"
                      accept=".jpg,.png,.pdf"
                    />
                  </label>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800 flex items-start gap-2">
                  <FiAlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>
                    Our team will manually review your submission. Only authentic documents will be
                    accepted. Any false information can result in the disapproval or suspension of
                    your account.
                  </span>
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  JPG or PNG format; maximum size of 20MB.
                </p>
              </div>

              {formData.certificates.length > 1 && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => removeCertificate(index)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addCertificate}
            className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
          >
            <FiPlus className="w-4 h-4" />
            Add another certificate
          </button>
        </div>
      )}
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Education</h2>
        <p className="text-gray-600">
          Tell students more about the higher education that you&apos;ve completed or are working on
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={formData.hasHigherEducation}
          onChange={(e) => updateFormData('hasHigherEducation', e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label className="text-sm text-gray-700">I don&apos;t have a higher education degree</label>
      </div>

      {!formData.hasHigherEducation && (
        <div className="space-y-4">
          {formData.education.map((edu, index) => (
            <div key={index} className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="University"
                  value={edu.university}
                  onChange={(e) => updateEducation(index, 'university', e.target.value)}
                  placeholder="E.g. Mount Royal University"
                />
                <Input
                  label="Degree"
                  value={edu.degree}
                  onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                  placeholder="E.g. Bachelor&apos;s degree in the English Language"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Degree type
                  </label>
                  <select
                    value={edu.degreeType}
                    onChange={(e) => updateEducation(index, 'degreeType', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Choose degree type...</option>
                    {DEGREE_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <Input
                  label="Specialization"
                  value={edu.specialization}
                  onChange={(e) => updateEducation(index, 'specialization', e.target.value)}
                  placeholder="E.g. Teaching English as a Foreign Language"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Year from"
                  type="number"
                  value={edu.yearsFrom}
                  onChange={(e) => updateEducation(index, 'yearsFrom', e.target.value)}
                  placeholder="2015"
                  min="1950"
                  max={new Date().getFullYear().toString()}
                />
                <Input
                  label="Year to"
                  type="number"
                  value={edu.yearsTo}
                  onChange={(e) => updateEducation(index, 'yearsTo', e.target.value)}
                  placeholder="2019"
                  min="1950"
                  max={(new Date().getFullYear() + 10).toString()}
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload diploma
                  </label>
                  <label className="w-full px-4 py-2 border border-gray-300 rounded-lg text-center text-gray-600 hover:bg-gray-50 cursor-pointer flex items-center justify-center gap-2">
                    <FiUpload className="w-4 h-4" />
                    {edu.file ? edu.file.name : 'Choose file'}
                    <input
                      type="file"
                      onChange={(e) => updateEducation(index, 'file', e.target.files?.[0] || null)}
                      className="hidden"
                      accept=".jpg,.png,.pdf"
                    />
                  </label>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-800 flex items-start gap-2">
                  <FiStar className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>
                    Get a &quot;Diploma verified&quot; badge! Upload your diploma to boost your credibility!
                    Our team will review it and add the badge to your profile. Once reviewed, your
                    files will be deleted.
                  </span>
                </p>
                <p className="text-xs text-green-700 mt-1">
                  JPG or PNG format; maximum size of 20MB.
                </p>
              </div>

              {formData.education.length > 1 && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addEducation}
            className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
          >
            <FiPlus className="w-4 h-4" />
            Add another education
          </button>
        </div>
      )}
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Description</h2>
        <p className="text-gray-600">
          This info will go on your public profile. Write it in the language you&apos;ll be teaching and
          make sure to follow our guidelines to get approved
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">1. Introduce yourself</h3>
        <p className="text-sm text-blue-800 mb-3">
          Show potential students who you are! Share your teaching experience and passion for
          education and briefly mention your interests and hobbies.
        </p>
        <ul className="text-sm text-blue-800 space-y-1">
          <li className="flex items-start gap-2">
            <FiCheck className="w-4 h-4 mt-0.5 flex-shrink-0" />
            Hello, my name is... and I&apos;m from...
          </li>
          <li className="flex items-start gap-2">
            <FiX className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" />
            Don&apos;t include your last name or present your information in a CV format
          </li>
        </ul>
      </div>

      <TextArea
        label="Profile description (this is the main text students see when deciding to book you)"
        value={formData.description}
        onChange={(e) => updateFormData('description', e.target.value)}
        placeholder="Introduce yourself and your background. Explain your teaching experience and methods. Describe what a typical lesson looks like. Share what results students can expect."
        minRows={8}
        maxRows={15}
        maxLength={2000}
        minLength={400}
        error={errors.description}
        helperText={
          formData.description.length >= 400
            ? "Great! Your description meets the minimum requirement"
            : `${400 - formData.description.length} more characters needed to meet the minimum requirement`
        }
      />
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      case 4:
        return renderStep4();
      case 5:
        return renderStep5();
      default:
        return renderStep1();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden p-8">
          <StepIndicator
            currentStep={currentStep}
            totalSteps={5}
            stepTitles={STEP_TITLES}
          />

          <div className="mt-8">
            {renderCurrentStep()}

            <div className="flex justify-between pt-8 mt-8 border-t border-gray-200">
              <Button
                variant="ghost"
                onClick={handleBack}
                disabled={currentStep === 1 || submitting}
              >
                Back
              </Button>

              <Button
                variant="primary"
                onClick={currentStep === 5 ? handleSubmit : handleNext}
                disabled={submitting}
              >
                {submitting
                  ? 'Submitting...'
                  : currentStep === 5
                    ? 'Submit Profile'
                    : 'Next'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
