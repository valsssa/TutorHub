"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { FiSave, FiPlus, FiTrash2 } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { tutors, subjects as subjectsApi } from "@/lib/api";
import { resolveAssetUrl } from "@/lib/media";
import type { TutorProfile, Subject } from "@/types";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import Input from "@/components/Input";
import TextArea from "@/components/TextArea";
import LoadingSpinner from "@/components/LoadingSpinner";
import AvatarUploader from "@/components/AvatarUploader";

const DAY_OPTIONS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
];

type SectionCardProps = {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
};

type SubjectForm = {
  id?: number;
  subject_id: number;
  proficiency_level: string;
  years_experience: number;
};

type CertificationForm = {
  id?: number;
  name: string;
  issuing_organization?: string;
  issue_date?: string;
  expiration_date?: string;
  credential_id?: string;
  credential_url?: string;
  document_url?: string;
  file?: File | null;
};

type EducationForm = {
  id?: number;
  institution: string;
  degree?: string;
  field_of_study?: string;
  start_year?: string;
  end_year?: string;
  description?: string;
  document_url?: string;
  file?: File | null;
};

type PricingOptionForm = {
  id?: number;
  title: string;
  description?: string;
  duration_minutes: string;
  price: string;
};

type AvailabilityForm = {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_recurring: boolean;
};

export default function TutorProfilePage() {
  return (
    <ProtectedRoute requiredRole="tutor">
      <TutorProfileContent />
    </ProtectedRoute>
  );
}

function SectionCard({
  title,
  description,
  children,
  footer,
}: SectionCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        {description && <p className="text-gray-600 mt-1">{description}</p>}
      </div>
      <div className="space-y-4">{children}</div>
      {footer && <div className="pt-4 border-t border-gray-100">{footer}</div>}
    </div>
  );
}

function TutorProfileContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<TutorProfile | null>(null);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [savingSection, setSavingSection] = useState<string | null>(null);

  const [aboutForm, setAboutForm] = useState({
    title: "",
    headline: "",
    bio: "",
    experience_years: 0,
  });
  const [languagesInput, setLanguagesInput] = useState("");
  const [description, setDescription] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [subjectsForm, setSubjectsForm] = useState<SubjectForm[]>([]);
  const [certificationsForm, setCertificationsForm] = useState<
    CertificationForm[]
  >([]);
  const [educationForm, setEducationForm] = useState<EducationForm[]>([]);
  const [pricingForm, setPricingForm] = useState<{
    hourly_rate: string;
    options: PricingOptionForm[];
  }>({
    hourly_rate: "",
    options: [],
  });
  const [availabilityForm, setAvailabilityForm] = useState<AvailabilityForm[]>(
    [],
  );
  const [availabilityTimezone, setAvailabilityTimezone] = useState("UTC");



  const setAboutFromProfile = useCallback((data: TutorProfile) => {
    setAboutForm({
      title: data.title || "",
      headline: data.headline || "",
      bio: data.bio || "",
      experience_years: data.experience_years || 0,
    });
    setLanguagesInput((data.languages || []).join(", "));
  }, []);

  const setSubjectsFromProfile = useCallback((data: TutorProfile) => {
    setSubjectsForm(
      (data.subjects || []).map((subject) => ({
        id: subject.id,
        subject_id: subject.subject_id,
        proficiency_level: subject.proficiency_level,
        years_experience: subject.years_experience || 0,
      })),
    );
  }, []);

  const setCertificationsFromProfile = useCallback((data: TutorProfile) => {
    setCertificationsForm(
      (data.certifications || []).map((cert) => ({
        id: cert.id,
        name: cert.name,
        issuing_organization: cert.issuing_organization || "",
        issue_date: cert.issue_date || "",
        expiration_date: cert.expiration_date || "",
        credential_id: cert.credential_id || "",
        credential_url: cert.credential_url || "",
        document_url: cert.document_url || "",
        file: null,
      })),
    );
  }, []);

  const setEducationFromProfile = useCallback((data: TutorProfile) => {
    setEducationForm(
      (data.educations || []).map((edu) => ({
        id: edu.id,
        institution: edu.institution || "",
        degree: edu.degree || "",
        field_of_study: edu.field_of_study || "",
        start_year: edu.start_year ? String(edu.start_year) : "",
        end_year: edu.end_year ? String(edu.end_year) : "",
        description: edu.description || "",
        document_url: edu.document_url || "",
        file: null,
      })),
    );
  }, []);

  const setPricingFromProfile = useCallback((data: TutorProfile) => {
    setPricingForm({
      hourly_rate: data.hourly_rate ? String(data.hourly_rate) : "",
      options: (data.pricing_options || []).map((option) => ({
        id: option.id,
        title: option.title,
        description: option.description || "",
        duration_minutes: option.duration_minutes
          ? String(option.duration_minutes)
          : "",
        price: option.price ? String(option.price) : "",
      })),
    });
  }, []);

  const setAvailabilityFromProfile = useCallback((data: TutorProfile) => {
    setAvailabilityForm(
      (data.availabilities || []).map((slot) => ({
        id: slot.id,
        day_of_week: slot.day_of_week,
        start_time: slot.start_time ? slot.start_time.slice(0, 5) : "09:00",
        end_time: slot.end_time ? slot.end_time.slice(0, 5) : "10:00",
        is_recurring: slot.is_recurring ?? true,
      })),
    );
    setAvailabilityTimezone(data.timezone || "UTC");
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [subjectsData, profileData] = await Promise.all([
          subjectsApi.list(),
          tutors.getMyProfile(),
        ]);
        setSubjectsList(subjectsData);
        setProfile(profileData);
        setAboutFromProfile(profileData);
        setDescription(profileData.description || "");
        setVideoUrl(profileData.video_url || "");
        setSubjectsFromProfile(profileData);
        setCertificationsFromProfile(profileData);
        setEducationFromProfile(profileData);
        setPricingFromProfile(profileData);
        setAvailabilityFromProfile(profileData);
      } catch (error) {
        const err = error as { response?: { data?: { detail?: string } } };
        showError(
          err.response?.data?.detail || "Failed to load tutor profile",
        );
      } finally{
        setLoading(false);
      }
    };

    fetchData();
  }, [
    setAboutFromProfile,
    setAvailabilityFromProfile,
    setCertificationsFromProfile,
    setEducationFromProfile,
    setPricingFromProfile,
    setSubjectsFromProfile,
    showError,
  ]);



  const runWithSaving = async (
    section: string,
    action: () => Promise<void>,
  ) => {
    setSavingSection(section);
    try {
      await action();
    } finally {
      setSavingSection(null);
    }
  };

  const isSaving = (section: string) => savingSection === section;

  const handleSaveAbout = async () => {
    if (!aboutForm.title.trim()) {
      showError("Title is required");
      return;
    }
    try {
      await runWithSaving("about", async () => {
        const languages = languagesInput
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);

        const updated = await tutors.updateAbout({
          title: aboutForm.title.trim(),
          headline: aboutForm.headline?.trim() || undefined,
          bio: aboutForm.bio?.trim() || undefined,
          experience_years: Number(aboutForm.experience_years) || 0,
          languages,
        });
        setProfile(updated);
        setAboutFromProfile(updated);
        showSuccess("About section updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      showError(
        err.response?.data?.detail || "Failed to update About section",
      );
    }
  };



  const handleSaveSubjects = async () => {
    if (!subjectsForm.length) {
      showError("Add at least one subject");
      return;
    }
    try {
      await runWithSaving("subjects", async () => {
        const payload = subjectsForm.map((subject) => ({
          subject_id: subject.subject_id,
          proficiency_level: subject.proficiency_level,
          years_experience: subject.years_experience ?? 0,
        }));
        const updated = await tutors.replaceSubjects(payload);
        setProfile(updated);
        setSubjectsFromProfile(updated);
        showSuccess("Subjects updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(err.response?.data?.detail || "Failed to update subjects");
    }
  };

  const handleSaveCertifications = async () => {
    const filtered = certificationsForm.filter((cert) => cert.name.trim());
    try {
      await runWithSaving("certifications", async () => {
        const files: Record<number, File> = {};
        const payload = filtered.map(({ id, file, document_url, ...rest }, index) => {
          if (file) {
            files[index] = file;
          }
          return {
            name: rest.name.trim(),
            issuing_organization: rest.issuing_organization?.trim() || undefined,
            issue_date: rest.issue_date || undefined,
            expiration_date: rest.expiration_date || undefined,
            credential_id: rest.credential_id?.trim() || undefined,
            credential_url: rest.credential_url?.trim() || undefined,
            document_url: file ? undefined : document_url || undefined,
          };
        });
        const updated = await tutors.replaceCertifications({
          certifications: payload,
          files: Object.keys(files).length ? files : undefined,
        });
        setProfile(updated);
        setCertificationsFromProfile(updated);
        showSuccess("Certifications updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      showError(
        err.response?.data?.detail || "Failed to update certifications",
      );
    }
  };

  const handleSaveEducation = async () => {
    const filtered = educationForm.filter((entry) => entry.institution.trim());
    try {
      await runWithSaving("education", async () => {
        const files: Record<number, File> = {};
        const payload = filtered.map(
          ({ id, start_year, end_year, file, document_url, ...rest }, index) => {
            if (file) {
              files[index] = file;
            }
            return {
              institution: rest.institution.trim(),
              degree: rest.degree?.trim() || undefined,
              field_of_study: rest.field_of_study?.trim() || undefined,
              start_year: start_year ? Number(start_year) : undefined,
              end_year: end_year ? Number(end_year) : undefined,
              description: rest.description?.trim() || undefined,
              document_url: file ? undefined : document_url || undefined,
            };
          },
        );
        const updated = await tutors.replaceEducation({
          education: payload,
          files: Object.keys(files).length ? files : undefined,
        });
        setProfile(updated);
        setEducationFromProfile(updated);
        showSuccess("Education updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(err.response?.data?.detail || "Failed to update education");
    }
  };

  const handleSaveDescription = async () => {
    if (!description.trim()) {
      showError("Description cannot be empty");
      return;
    }
    try {
      await runWithSaving("description", async () => {
        const updated = await tutors.updateDescription({
          description: description.trim(),
        });
        setProfile(updated);
        setDescription(updated.description || "");
        showSuccess("Description updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(err.response?.data?.detail || "Failed to update description");
    }
  };

  const handleSaveVideo = async () => {
    if (!videoUrl.trim()) {
      showError("Video URL cannot be empty");
      return;
    }
    try {
      await runWithSaving("video", async () => {
        const updated = await tutors.updateVideo({
          video_url: videoUrl.trim(),
        });
        setProfile(updated);
        setVideoUrl(updated.video_url || "");
        showSuccess("Video updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(err.response?.data?.detail || "Failed to update video");
    }
  };

  const handleSavePricing = async () => {
    if (!profile) {
      showError("Profile not loaded");
      return;
    }
    if (!pricingForm.hourly_rate) {
      showError("Hourly rate is required");
      return;
    }
    const hourlyRate = Number(pricingForm.hourly_rate);
    if (Number.isNaN(hourlyRate) || hourlyRate <= 0) {
      showError("Hourly rate must be a positive number");
      return;
    }

    const payloadOptions: Array<{
      title: string;
      description?: string;
      duration_minutes: number;
      price: number;
    }> = [];
    for (const option of pricingForm.options) {
      if (!option.title.trim()) {
        continue;
      }
      const duration = Number(option.duration_minutes);
      const priceValue = Number(option.price);
      if (!duration || duration <= 0) {
        showError("Package duration must be a positive number of minutes");
        return;
      }
      if (!priceValue || priceValue <= 0) {
        showError("Package price must be a positive number");
        return;
      }
      payloadOptions.push({
        title: option.title.trim(),
        description: option.description?.trim() || undefined,
        duration_minutes: duration,
        price: priceValue,
      });
    }

    try {
      await runWithSaving("pricing", async () => {
        const updated = await tutors.updatePricing({
          hourly_rate: hourlyRate,
          pricing_options: payloadOptions,
          version: profile.version,
        });
        setProfile(updated);
        setPricingFromProfile(updated);
        showSuccess("Pricing updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string }; status?: number }; message?: string };
      if (err.response?.status === 409) {
        showError("Profile was updated by another session. Refreshing...");
        window.location.reload();
      } else {
        showError(err.response?.data?.detail || "Failed to update pricing");
      }
    }
  };

  const handleSaveAvailability = async () => {
    if (!profile) {
      showError("Profile not loaded");
      return;
    }
    const payload = availabilityForm.map(({ id, ...slot }) => ({
      ...slot,
      start_time: slot.start_time,
      end_time: slot.end_time,
    }));
    const timezone = availabilityTimezone.trim() || "UTC";
    try {
      await runWithSaving("availability", async () => {
        const updated = await tutors.replaceAvailability({
          availability: payload,
          timezone,
          version: profile.version,
        });
        setProfile(updated);
        setAvailabilityFromProfile(updated);
        showSuccess("Availability updated");
      });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string }; status?: number } };
      if (err.response?.status === 409) {
        showError("Profile was updated by another session. Refreshing...");
        window.location.reload();
      } else {
        showError(
          err.response?.data?.detail || "Failed to update availability",
        );
      }
    }
  };

  const addSubject = () => {
    if (!subjectsList.length) {
      showError("No subjects available. Please contact support.");
      return;
    }
    const defaultSubjectId = subjectsList[0]?.id || 0;
    setSubjectsForm((prev) => [
      ...prev,
      {
        subject_id: defaultSubjectId,
        proficiency_level: "B2",
        years_experience: 0,
      },
    ]);
  };

  const updateSubject = (
    index: number,
    field: keyof SubjectForm,
    value: string | number,
  ) => {
    setSubjectsForm((prev) =>
      prev.map((subject, idx) =>
        idx === index
          ? {
              ...subject,
              [field]: field === "years_experience" ? Number(value) : value,
            }
          : subject,
      ),
    );
  };

  const removeSubject = (index: number) => {
    setSubjectsForm((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addCertification = () => {
    setCertificationsForm((prev) => [
      ...prev,
      {
        name: "",
        issuing_organization: "",
        issue_date: "",
        expiration_date: "",
        credential_id: "",
        credential_url: "",
        document_url: "",
        file: null,
      },
    ]);
  };

  const updateCertification = (
    index: number,
    field: keyof CertificationForm,
    value: string,
  ) => {
    setCertificationsForm((prev) =>
      prev.map((cert, idx) =>
        idx === index ? { ...cert, [field]: value } : cert,
      ),
    );
  };

  const handleCertificationFileChange = (index: number, file: File | null) => {
    setCertificationsForm((prev) =>
      prev.map((cert, idx) =>
        idx === index
          ? { ...cert, file }
          : cert,
      ),
    );
  };

  const clearCertificationDocument = (index: number) => {
    setCertificationsForm((prev) =>
      prev.map((cert, idx) =>
        idx === index
          ? {
              ...cert,
              file: null,
              document_url: cert.file ? cert.document_url : undefined,
            }
          : cert,
      ),
    );
  };

  const removeCertification = (index: number) => {
    setCertificationsForm((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addEducation = () => {
    setEducationForm((prev) => [
      ...prev,
      {
        institution: "",
        degree: "",
        field_of_study: "",
        start_year: "",
        end_year: "",
        description: "",
        document_url: "",
        file: null,
      },
    ]);
  };

  const updateEducation = (
    index: number,
    field: keyof EducationForm,
    value: string,
  ) => {
    setEducationForm((prev) =>
      prev.map((entry, idx) =>
        idx === index ? { ...entry, [field]: value } : entry,
      ),
    );
  };

  const handleEducationFileChange = (index: number, file: File | null) => {
    setEducationForm((prev) =>
      prev.map((entry, idx) =>
        idx === index
          ? { ...entry, file }
          : entry,
      ),
    );
  };

  const clearEducationDocument = (index: number) => {
    setEducationForm((prev) =>
      prev.map((entry, idx) =>
        idx === index
          ? {
              ...entry,
              file: null,
              document_url: entry.file ? entry.document_url : undefined,
            }
          : entry,
      ),
    );
  };

  const removeEducation = (index: number) => {
    setEducationForm((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addPricingOption = () => {
    setPricingForm((prev) => ({
      ...prev,
      options: [
        ...prev.options,
        {
          title: "",
          description: "",
          duration_minutes: "60",
          price: "",
        },
      ],
    }));
  };

  const updatePricingOption = (
    index: number,
    field: keyof PricingOptionForm,
    value: string,
  ) => {
    setPricingForm((prev) => ({
      ...prev,
      options: prev.options.map((option, idx) =>
        idx === index ? { ...option, [field]: value } : option,
      ),
    }));
  };

  const removePricingOption = (index: number) => {
    setPricingForm((prev) => ({
      ...prev,
      options: prev.options.filter((_, idx) => idx !== index),
    }));
  };

  const addAvailabilitySlot = () => {
    setAvailabilityForm((prev) => [
      ...prev,
      {
        day_of_week: 1,
        start_time: "09:00",
        end_time: "10:00",
        is_recurring: true,
      },
    ]);
  };

  const updateAvailabilitySlot = (
    index: number,
    field: keyof AvailabilityForm,
    value: string | boolean | number,
  ) => {
    setAvailabilityForm((prev) =>
      prev.map((slot, idx) =>
        idx === index
          ? {
              ...slot,
              [field]: field === "day_of_week" ? Number(value) : value,
            }
          : slot,
      ),
    );
  };

  const removeAvailabilitySlot = (index: number) => {
    setAvailabilityForm((prev) => prev.filter((_, idx) => idx !== index));
  };

  const profileStatus = useMemo(() => {
    if (!profile) return "Loading...";
    return profile.is_approved ? "Approved" : "Pending approval";
  }, [profile]);

  const [activeSection, setActiveSection] = useState("about");

  const sections = [
    { id: "about", label: "About", icon: "👤" },
    { id: "photo", label: "Profile Photo", icon: "📷" },
    { id: "subjects", label: "Subjects", icon: "📚" },
    { id: "certifications", label: "Certifications", icon: "🏆" },
    { id: "education", label: "Education", icon: "🎓" },
    { id: "description", label: "Description", icon: "📝" },
    { id: "video", label: "Intro Video", icon: "🎥" },
    { id: "pricing", label: "Pricing", icon: "💰" },
    { id: "availability", label: "Availability", icon: "📅" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Tutor Profile</h1>
              <p className="text-sm text-gray-600 mt-1">
                Status:{" "}
                <span className={`font-medium ${profile?.is_approved ? 'text-green-600' : 'text-amber-600'}`}>
                  {profileStatus}
                </span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => router.push("/dashboard")}>
              ← Back to Dashboard
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Left Sidebar Navigation */}
          <aside className="w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm p-4 sticky top-24">
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeSection === section.id
                        ? "bg-primary-50 text-primary-700 font-semibold"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-xl">{section.icon}</span>
                    <span className="text-sm">{section.label}</span>
                  </button>
                ))}
              </nav>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1">
            {/* About Section */}
            {activeSection === "about" && (
              <SectionCard
                title="About"
                description="Introduce yourself to students with a compelling title, headline, and short biography."
                footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveAbout}
                disabled={isSaving("about")}
                className="flex items-center gap-2"
              >
                <FiSave /> {isSaving("about") ? "Saving..." : "Save About"}
              </Button>
            </div>
          }
        >
          <Input
            label="Title"
            placeholder="Experienced Math Tutor"
            value={aboutForm.title}
            onChange={(e) =>
              setAboutForm({ ...aboutForm, title: e.target.value })
            }
            required
          />
          <Input
            label="Headline"
            placeholder="Helping students succeed for over 5 years"
            value={aboutForm.headline}
            onChange={(e) =>
              setAboutForm({ ...aboutForm, headline: e.target.value })
            }
          />
          <TextArea
            label="Short bio (shown on your public profile)"
            value={aboutForm.bio}
            onChange={(e) =>
              setAboutForm({ ...aboutForm, bio: e.target.value })
            }
            placeholder="Who are you as a teacher? What's your approach? What can students expect from lessons with you?"
            minRows={4}
            maxRows={8}
            maxLength={600}
            minLength={80}
            helperText="A compelling bio helps students decide if you're the right fit for them"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Years of Experience"
              type="number"
              min={0}
              value={aboutForm.experience_years}
              onChange={(e) =>
                setAboutForm({
                  ...aboutForm,
                  experience_years: Number(e.target.value) || 0,
                })
              }
            />
            <Input
              label="Languages"
              placeholder="en, es, fr"
              value={languagesInput}
              onChange={(e) => setLanguagesInput(e.target.value)}
              helperText="Use ISO 639-1 codes (e.g., en, es, fr, de). Separate with commas."
            />
          </div>
        </SectionCard>
            )}

            {/* Profile Photo Section */}
            {activeSection === "photo" && (
              <AvatarUploader
                title="Profile Photo"
                description="Use a clear, professional photo to build trust with students. Upload a square JPG or PNG under 2MB."
                allowRemoval
              />
            )}

            {/* Subjects Section */}
            {activeSection === "subjects" && (
              <SectionCard
                title="Subjects"
          description="Manage the subjects you teach and your proficiency."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveSubjects}
                disabled={isSaving("subjects")}
                className="flex items-center gap-2"
              >
                <FiSave />{" "}
                {isSaving("subjects") ? "Saving..." : "Save Subjects"}
              </Button>
            </div>
          }
        >
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Add all subjects you can teach and highlight your strengths.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={addSubject}
              className="flex items-center gap-2"
            >
              <FiPlus /> Add Subject
            </Button>
          </div>
          <div className="space-y-4">
            {subjectsForm.map((subject, index) => (
              <div
                key={`subject-${index}`}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subject
                    </label>
                    <select
                      value={subject.subject_id}
                      onChange={(e) =>
                        updateSubject(
                          index,
                          "subject_id",
                          Number(e.target.value),
                        )
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      {subjectsList.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Proficiency
                    </label>
                    <select
                      value={subject.proficiency_level}
                      onChange={(e) =>
                        updateSubject(
                          index,
                          "proficiency_level",
                          e.target.value,
                        )
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="A1">A1 - Beginner</option>
                      <option value="A2">A2 - Elementary</option>
                      <option value="B1">B1 - Intermediate</option>
                      <option value="B2">B2 - Upper Intermediate</option>
                      <option value="C1">C1 - Advanced</option>
                      <option value="C2">C2 - Mastery</option>
                      <option value="Native">Native</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <Input
                      label="Years Exp."
                      type="number"
                      min={0}
                      value={subject.years_experience}
                      onChange={(e) =>
                        updateSubject(
                          index,
                          "years_experience",
                          Number(e.target.value),
                        )
                      }
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeSubject(index)}
                      className="mt-7 text-red-600 hover:bg-red-50"
                    >
                      <FiTrash2 />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {!subjectsForm.length && (
              <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-600">
                No subjects added yet. Click “Add Subject” to get started.
              </div>
            )}
          </div>
        </SectionCard>
            )}

            {/* Certifications Section */}
            {activeSection === "certifications" && (
              <SectionCard
                title="Certifications"
          description="Showcase certifications and credentials that verify your expertise."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveCertifications}
                disabled={isSaving("certifications")}
                className="flex items-center gap-2"
              >
                <FiSave />{" "}
                {isSaving("certifications")
                  ? "Saving..."
                  : "Save Certifications"}
              </Button>
            </div>
          }
        >
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Include the issuing organization and dates for each certification.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={addCertification}
              className="flex items-center gap-2"
            >
              <FiPlus /> Add Certification
            </Button>
          </div>
          <div className="space-y-4">
            {certificationsForm.map((cert, index) => (
              <div
                key={`cert-${index}`}
                className="border border-gray-200 rounded-lg p-4 space-y-4"
              >
                <Input
                  label="Certification Name"
                  value={cert.name}
                  onChange={(e) =>
                    updateCertification(index, "name", e.target.value)
                  }
                  placeholder="TESOL Certification"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Issuing Organization"
                    value={cert.issuing_organization || ""}
                    onChange={(e) =>
                      updateCertification(
                        index,
                        "issuing_organization",
                        e.target.value,
                      )
                    }
                  />
                  <Input
                    label="Credential ID (optional)"
                    value={cert.credential_id || ""}
                    onChange={(e) =>
                      updateCertification(
                        index,
                        "credential_id",
                        e.target.value,
                      )
                    }
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Issue Date"
                    type="date"
                    value={cert.issue_date || ""}
                    onChange={(e) =>
                      updateCertification(index, "issue_date", e.target.value)
                    }
                  />
                  <Input
                    label="Expiration Date"
                    type="date"
                    value={cert.expiration_date || ""}
                    onChange={(e) =>
                      updateCertification(
                        index,
                        "expiration_date",
                        e.target.value,
                      )
                    }
                  />
                </div>
                <Input
                  label="Credential URL"
                  type="url"
                  value={cert.credential_url || ""}
                  onChange={(e) =>
                    updateCertification(index, "credential_url", e.target.value)
                  }
                  placeholder="https://..."
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Certification Document (optional)
                  </label>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,application/pdf"
                    onChange={(e) =>
                      handleCertificationFileChange(
                        index,
                        e.target.files && e.target.files[0]
                          ? e.target.files[0]
                          : null,
                      )
                    }
                    className="w-full text-sm text-gray-600"
                  />
                  <div className="mt-2 text-sm text-gray-600">
                    {cert.file ? (
                      <span>Selected: {cert.file.name}</span>
                    ) : cert.document_url ? (
                      <a
                        href={resolveAssetUrl(cert.document_url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 underline"
                      >
                        View current document
                      </a>
                    ) : (
                      <span>No document uploaded</span>
                    )}
                  </div>
                  {(cert.document_url || cert.file) && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => clearCertificationDocument(index)}
                      className="mt-2 text-red-600 hover:bg-red-50"
                    >
                      {cert.file ? "Clear Selection" : "Remove Document"}
                    </Button>
                  )}
                </div>
                <div className="flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeCertification(index)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <FiTrash2 />
                  </Button>
                </div>
              </div>
            ))}
            {!certificationsForm.length && (
              <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-600">
                No certifications added yet.
              </div>
            )}
          </div>
        </SectionCard>
            )}

            {/* Education Section */}
            {activeSection === "education" && (
              <SectionCard
                title="Education"
          description="Highlight formal education relevant to your tutoring expertise."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveEducation}
                disabled={isSaving("education")}
                className="flex items-center gap-2"
              >
                <FiSave />{" "}
                {isSaving("education") ? "Saving..." : "Save Education"}
              </Button>
            </div>
          }
        >
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Share degrees, institutions, and fields of study.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={addEducation}
              className="flex items-center gap-2"
            >
              <FiPlus /> Add Education
            </Button>
          </div>
          <div className="space-y-4">
            {educationForm.map((entry, index) => (
              <div
                key={`education-${index}`}
                className="border border-gray-200 rounded-lg p-4 space-y-4"
              >
                <Input
                  label="Institution"
                  value={entry.institution}
                  onChange={(e) =>
                    updateEducation(index, "institution", e.target.value)
                  }
                  placeholder="University of Education"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Degree"
                    value={entry.degree || ""}
                    onChange={(e) =>
                      updateEducation(index, "degree", e.target.value)
                    }
                    placeholder="Master of Arts"
                  />
                  <Input
                    label="Field of Study"
                    value={entry.field_of_study || ""}
                    onChange={(e) =>
                      updateEducation(index, "field_of_study", e.target.value)
                    }
                    placeholder="English Literature"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Start Year"
                    type="number"
                    value={entry.start_year || ""}
                    onChange={(e) =>
                      updateEducation(index, "start_year", e.target.value)
                    }
                  />
                  <Input
                    label="End Year"
                    type="number"
                    value={entry.end_year || ""}
                    onChange={(e) =>
                      updateEducation(index, "end_year", e.target.value)
                    }
                  />
                </div>
                <TextArea
                  label="Description (optional - highlights relevant achievements)"
                  value={entry.description || ""}
                  onChange={(e) =>
                    updateEducation(index, "description", e.target.value)
                  }
                  placeholder="What did you focus on? What achievements are relevant to teaching? What skills did you develop?"
                  minRows={3}
                  maxRows={6}
                  maxLength={500}
                  helperText="Focus on aspects that demonstrate your expertise in your teaching subjects"
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Credential Document (optional)
                  </label>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,application/pdf"
                    onChange={(e) =>
                      handleEducationFileChange(
                        index,
                        e.target.files && e.target.files[0]
                          ? e.target.files[0]
                          : null,
                      )
                    }
                    className="w-full text-sm text-gray-600"
                  />
                  <div className="mt-2 text-sm text-gray-600">
                    {entry.file ? (
                      <span>Selected: {entry.file.name}</span>
                    ) : entry.document_url ? (
                      <a
                        href={resolveAssetUrl(entry.document_url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 underline"
                      >
                        View current document
                      </a>
                    ) : (
                      <span>No document uploaded</span>
                    )}
                  </div>
                  {(entry.document_url || entry.file) && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => clearEducationDocument(index)}
                      className="mt-2 text-red-600 hover:bg-red-50"
                    >
                      {entry.file ? "Clear Selection" : "Remove Document"}
                    </Button>
                  )}
                </div>
                <div className="flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <FiTrash2 />
                  </Button>
                </div>
              </div>
            ))}
            {!educationForm.length && (
              <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-600">
                No education history added yet.
              </div>
            )}
          </div>
        </SectionCard>
            )}

            {/* Description Section */}
            {activeSection === "description" && (
              <SectionCard
                title="Detailed Description"
          description="Provide a comprehensive overview of your teaching style, approach, and what students can expect."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveDescription}
                disabled={isSaving("description")}
                className="flex items-center gap-2"
              >
                <FiSave />{" "}
                {isSaving("description") ? "Saving..." : "Save Description"}
              </Button>
            </div>
          }
        >
          <TextArea
            label="Full description (this is the main text students see on your profile)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What's your lesson structure? How do you adapt to different student needs? What makes your teaching effective? What results can students expect?"
            minRows={6}
            maxRows={12}
            maxLength={2000}
            minLength={200}
            helperText="A detailed description helps students understand exactly what they'll get from lessons with you"
          />
        </SectionCard>
            )}

            {/* Intro Video Section */}
            {activeSection === "video" && (
              <SectionCard
                title="Intro Video"
          description="Share a video introduction to build rapport with students before the first session."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveVideo}
                disabled={isSaving("video")}
                className="flex items-center gap-2"
              >
                <FiSave /> {isSaving("video") ? "Saving..." : "Save Video"}
              </Button>
            </div>
          }
        >
          <Input
            label="Video URL"
            type="url"
            placeholder="https://youtube.com/..."
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
          />
          <p className="text-sm text-gray-500">
            Use a publicly accessible link (YouTube, Vimeo, Loom, etc.).
          </p>
        </SectionCard>
            )}

            {/* Availability Section */}
            {activeSection === "availability" && (
              <SectionCard
                title="Availability"
          description="Set recurring availability slots to make scheduling effortless."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSaveAvailability}
                disabled={isSaving("availability")}
                className="flex items-center gap-2"
              >
                <FiSave />{" "}
                {isSaving("availability") ? "Saving..." : "Save Availability"}
              </Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Timezone"
              value={availabilityTimezone}
              onChange={(e) => setAvailabilityTimezone(e.target.value)}
              helperText="Use a valid IANA timezone (e.g., America/New_York)"
            />
          </div>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Add multiple time slots to cover different days.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={addAvailabilitySlot}
              className="flex items-center gap-2"
            >
              <FiPlus /> Add Slot
            </Button>
          </div>
          <div className="space-y-4">
            {availabilityForm.map((slot, index) => (
              <div
                key={`availability-${index}`}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Day
                    </label>
                    <select
                      value={slot.day_of_week}
                      onChange={(e) =>
                        updateAvailabilitySlot(
                          index,
                          "day_of_week",
                          Number(e.target.value),
                        )
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      {DAY_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Input
                    label="Start Time"
                    type="time"
                    value={slot.start_time}
                    onChange={(e) =>
                      updateAvailabilitySlot(
                        index,
                        "start_time",
                        e.target.value,
                      )
                    }
                  />
                  <Input
                    label="End Time"
                    type="time"
                    value={slot.end_time}
                    onChange={(e) =>
                      updateAvailabilitySlot(index, "end_time", e.target.value)
                    }
                  />
                  <div className="flex items-center gap-2 pt-6">
                    <input
                      id={`recurring-${index}`}
                      type="checkbox"
                      checked={slot.is_recurring}
                      onChange={(e) =>
                        updateAvailabilitySlot(
                          index,
                          "is_recurring",
                          e.target.checked,
                        )
                      }
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded"
                    />
                    <label
                      htmlFor={`recurring-${index}`}
                      className="text-sm text-gray-700"
                    >
                      Recurring
                    </label>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAvailabilitySlot(index)}
                      className="text-red-600 hover:bg-red-50"
                    >
                      <FiTrash2 />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {!availabilityForm.length && (
              <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-600">
                No availability set. Add slots to let students book with you.
              </div>
            )}
          </div>
        </SectionCard>
            )}

            {/* Pricing Section */}
            {activeSection === "pricing" && (
              <SectionCard
                title="Pricing"
          description="Define your hourly rate and optional packages to motivate repeat bookings."
          footer={
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleSavePricing}
                disabled={isSaving("pricing")}
                className="flex items-center gap-2"
              >
                <FiSave /> {isSaving("pricing") ? "Saving..." : "Save Pricing"}
              </Button>
            </div>
          }
        >
          <Input
            label="Hourly Rate (USD)"
            type="number"
            min={1}
            step="0.01"
            value={pricingForm.hourly_rate}
            onChange={(e) =>
              setPricingForm((prev) => ({
                ...prev,
                hourly_rate: e.target.value,
              }))
            }
          />
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Optional: Offer lesson packages with set durations and prices.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={addPricingOption}
              className="flex items-center gap-2"
            >
              <FiPlus /> Add Package
            </Button>
          </div>
          <div className="space-y-4">
            {pricingForm.options.map((option, index) => (
              <div
                key={`pricing-${index}`}
                className="border border-gray-200 rounded-lg p-4 space-y-4"
              >
                <Input
                  label="Package Title"
                  value={option.title}
                  onChange={(e) =>
                    updatePricingOption(index, "title", e.target.value)
                  }
                  placeholder="5-Lesson Bundle"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Duration (minutes)"
                    type="number"
                    min={15}
                    value={option.duration_minutes}
                    onChange={(e) =>
                      updatePricingOption(
                        index,
                        "duration_minutes",
                        e.target.value,
                      )
                    }
                  />
                  <Input
                    label="Price (USD)"
                    type="number"
                    min={1}
                    step="0.01"
                    value={option.price}
                    onChange={(e) =>
                      updatePricingOption(index, "price", e.target.value)
                    }
                  />
                </div>
                <TextArea
                  label="Package description (helps students choose the right option)"
                  value={option.description || ""}
                  onChange={(e) =>
                    updatePricingOption(index, "description", e.target.value)
                  }
                  placeholder="What's included? What makes this package valuable? Who is it best suited for?"
                  minRows={3}
                  maxRows={5}
                  maxLength={300}
                  helperText="Clear package descriptions increase bookings"
                />
                <div className="flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removePricingOption(index)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <FiTrash2 />
                  </Button>
                </div>
              </div>
            ))}
            {!pricingForm.options.length && (
              <div className="text-center py-6 bg-gray-50 rounded-lg text-gray-600">
                No packages added. You can still save your hourly rate above.
              </div>
            )}
          </div>
        </SectionCard>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
