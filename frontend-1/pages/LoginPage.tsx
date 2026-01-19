import React, { useState, useEffect } from 'react';
import { BookOpen, ArrowRight, Github, ArrowLeft, Mail, Lock, CheckCircle, ExternalLink, User as UserIcon } from 'lucide-react';
import { UserRole, User } from '../domain/types';
import { useAuth } from '../contexts/AuthContext';

interface LoginPageProps {
    onLogin: (user: User, nextView: any) => void;
    setNotification: (msg: string) => void;
    initialView?: 'LOGIN' | 'SIGNUP';
    initialRole?: UserRole;
}

type AuthView = 'LOGIN' | 'SIGNUP' | 'VERIFY_EMAIL' | 'FORGOT_PASSWORD' | 'EMAIL_SENT' | 'RESET_PASSWORD';

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, setNotification, initialView, initialRole }) => {
    const { login } = useAuth();
    const [view, setView] = useState<AuthView>((initialView as AuthView) || 'LOGIN');
    
    // Login State
    const [role, setRole] = useState<UserRole>(initialRole || UserRole.STUDENT);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    
    // Signup State
    const [signupName, setSignupName] = useState('');
    const [signupEmail, setSignupEmail] = useState('');
    const [signupPassword, setSignupPassword] = useState('');
    const [signupRole, setSignupRole] = useState<UserRole>(initialRole || UserRole.STUDENT);
    
    // Verification State
    const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);

    // Reset Flow State
    const [resetEmail, setResetEmail] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (initialView) setView(initialView as AuthView);
        if (initialRole) {
            setRole(initialRole);
            setSignupRole(initialRole);
        }
    }, [initialView, initialRole]);

    // --- Handlers ---

    const handleLogin = async (e: React.FormEvent) => {
      e.preventDefault();
      
      if (!email || !password) {
          setNotification("Please enter your email and password.");
          return;
      }

      setLoading(true);
      
      try {
          await login(email, role);
          // Determine next view based on role
          let nextView = 'home';
          if (role === UserRole.TUTOR) nextView = 'tutor-dashboard';
          if (role === UserRole.ADMIN || role === UserRole.OWNER) nextView = 'admin-dashboard';
          
          // Trigger the router navigation callback
          // We pass a dummy user object because onLogin expects it, but AuthContext holds the real state now.
          // Ideally onLogin should just take the view, but preserving signature for AppRouter compatibility.
          onLogin({} as User, nextView); 
      } catch (err) {
          console.error(err);
          setNotification("Login failed. Please try again.");
      } finally {
          setLoading(false);
      }
    };

    const handleSignupSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!signupName || !signupEmail || !signupPassword) {
            setNotification("Please fill in all fields");
            return;
        }
        setLoading(true);
        // Simulate API call to register and send email
        setTimeout(() => {
            setLoading(false);
            setView('VERIFY_EMAIL');
            setNotification(`Verification code sent to ${signupEmail}`);
        }, 800);
    };

    const handleVerificationCodeChange = (index: number, value: string) => {
        if (value.length > 1) return;
        const newCode = [...verificationCode];
        newCode[index] = value;
        setVerificationCode(newCode);

        // Auto-focus next input
        if (value && index < 5) {
            const nextInput = document.getElementById(`code-${index + 1}`);
            nextInput?.focus();
        }
    };

    const handleVerificationSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const code = verificationCode.join('');
        if (code.length !== 6) {
            setNotification("Please enter the complete 6-digit code");
            return;
        }

        setLoading(true);
        // Simulate API verification & Login
        try {
            // In a real app, verify first, then login
            await login(signupEmail, signupRole);
            
            setNotification("Email verified successfully! Logging you in...");
            let nextView = 'home';
            if (signupRole === UserRole.TUTOR) nextView = 'tutor-dashboard';
            
            onLogin({} as User, nextView);
        } catch (error) {
            setNotification("Verification failed.");
        } finally {
            setLoading(false);
        }
    };

    const handleForgotPasswordSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        // Simulate API call to send email
        setTimeout(() => {
            setLoading(false);
            setView('EMAIL_SENT');
        }, 800);
    };

    const handleResetPasswordSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            setNotification("Passwords do not match");
            return;
        }
        if (newPassword.length < 6) {
             setNotification("Password must be at least 6 characters");
             return;
        }
        
        setLoading(true);
        // Simulate API call to reset password
        setTimeout(() => {
            setLoading(false);
            setNotification("Password reset successfully. Please login.");
            setView('LOGIN');
            // Clear fields
            setPassword('');
            setNewPassword('');
            setConfirmPassword('');
        }, 1000);
    };

    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-950 relative overflow-hidden transition-colors duration-200 py-12">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
           <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-emerald-600/10 rounded-full blur-[100px]" />
           <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px]" />
        </div>

        <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-2xl z-10 animate-in fade-in zoom-in-95 duration-300">
           
           {/* --- VIEW: LOGIN --- */}
           {view === 'LOGIN' && (
             <>
               <div className="text-center mb-8">
                  <div className="w-12 h-12 bg-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-900/20">
                     <BookOpen className="text-white" size={24} />
                  </div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Welcome Back</h1>
                  <p className="text-slate-500 dark:text-slate-400">Sign in to continue your learning journey</p>
               </div>

               <form onSubmit={handleLogin} className="space-y-4">
                  <div>
                     <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Email Address</label>
                     <input 
                        type="email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500"
                        placeholder="name@example.com"
                     />
                  </div>
                  <div>
                     <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Password</label>
                     <input 
                        type="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500"
                        placeholder="••••••••"
                     />
                  </div>

                  <div className="flex items-center justify-between text-sm">
                     <label className="flex items-center gap-2 text-slate-500 dark:text-slate-400 cursor-pointer">
                        <input type="checkbox" className="rounded bg-slate-200 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-emerald-500 focus:ring-0" />
                        Remember me
                     </label>
                     <button 
                        type="button"
                        onClick={() => setView('FORGOT_PASSWORD')}
                        className="text-emerald-500 hover:underline focus:outline-none"
                     >
                        Forgot password?
                     </button>
                  </div>

                  <button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2 mt-2"
                  >
                    {loading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <>Sign In <ArrowRight size={18} /></>
                    )}
                  </button>
               </form>

               <div className="text-center mt-6">
                   <p className="text-sm text-slate-500 dark:text-slate-400">
                       Don't have an account? <button onClick={() => setView('SIGNUP')} className="text-emerald-600 dark:text-emerald-400 font-bold hover:underline">Sign up</button>
                   </p>
               </div>

               {/* Social Login Section */}
               <div className="mt-6">
                  <div className="relative my-4">
                      <div className="absolute inset-0 flex items-center">
                          <div className="w-full border-t border-slate-200 dark:border-slate-800"></div>
                      </div>
                      <div className="relative flex justify-center text-sm">
                          <span className="px-2 bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400">Or continue with</span>
                      </div>
                  </div>
                  
                  <div className="flex justify-center gap-4">
                      <button 
                          type="button"
                          onClick={() => setNotification("Google login simulated")}
                          className="flex items-center justify-center w-10 h-10 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
                          title="Sign in with Google"
                      >
                          <svg className="w-5 h-5" viewBox="0 0 24 24">
                              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                          </svg>
                      </button>
                      <button 
                          type="button"
                          onClick={() => setNotification("GitHub login simulated")}
                          className="flex items-center justify-center w-10 h-10 bg-slate-900 dark:bg-slate-800 border border-slate-800 dark:border-slate-700 rounded-full hover:bg-slate-800 dark:hover:bg-slate-700 transition-colors text-white shadow-sm"
                          title="Sign in with GitHub"
                      >
                          <Github size={20} />
                      </button>
                  </div>
               </div>
               
               <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                   <p className="text-xs text-center text-slate-500 dark:text-slate-600 mb-3">Demo Credentials (Click to fill)</p>
                   <div className="flex gap-2 justify-center flex-wrap">
                       <button 
                         type="button"
                         onClick={() => { setEmail('alex@edu.com'); setPassword('password'); setRole(UserRole.STUDENT); }}
                         className="px-3 text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 py-2 rounded border border-slate-200 dark:border-slate-700 transition-colors"
                       >
                         Student
                       </button>
                       <button 
                         type="button"
                         onClick={() => { setEmail('elena@edu.com'); setPassword('password'); setRole(UserRole.TUTOR); }}
                         className="px-3 text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 py-2 rounded border border-slate-200 dark:border-slate-700 transition-colors"
                       >
                         Tutor
                       </button>
                        <button 
                         type="button"
                         onClick={() => { setEmail('admin@edu.com'); setPassword('admin123'); setRole(UserRole.ADMIN); }}
                         className="px-3 text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 py-2 rounded border border-slate-200 dark:border-slate-700 transition-colors"
                       >
                         Admin
                       </button>
                        <button 
                         type="button"
                         onClick={() => { setEmail('owner@edu.com'); setPassword('owner123'); setRole(UserRole.OWNER); }}
                         className="px-3 text-[10px] bg-slate-900 dark:bg-slate-200 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-300 py-2 rounded border border-slate-900 dark:border-slate-200 transition-colors font-bold"
                       >
                         Owner
                       </button>
                   </div>
               </div>
             </>
           )}

           {/* --- SIGNUP, VERIFY, FORGOT, RESET Views remain same structure but handled by state --- */}
           {/* (Content for these views is maintained from previous versions but uses handleLogin/handleSignup logic) */}
           {view === 'SIGNUP' && (
               <div className="animate-in slide-in-from-right duration-300">
                   <button 
                        onClick={() => setView('LOGIN')}
                        className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 text-sm mb-6 transition-colors"
                    >
                        <ArrowLeft size={16} /> Back to Login
                    </button>
                   <div className="text-center mb-6">
                      <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center mx-auto mb-4 text-emerald-600 dark:text-emerald-400">
                         <UserIcon size={24} />
                      </div>
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Create Account</h2>
                      <p className="text-slate-500 dark:text-slate-400">Join EduConnect today.</p>
                   </div>

                   <form onSubmit={handleSignupSubmit} className="space-y-4">
                       <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg mb-2">
                           <button
                               type="button"
                               onClick={() => setSignupRole(UserRole.STUDENT)}
                               className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all ${signupRole === UserRole.STUDENT ? 'bg-white dark:bg-slate-700 shadow text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
                           >
                               Student
                           </button>
                           <button
                               type="button"
                               onClick={() => setSignupRole(UserRole.TUTOR)}
                               className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all ${signupRole === UserRole.TUTOR ? 'bg-white dark:bg-slate-700 shadow text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
                           >
                               Tutor
                           </button>
                       </div>

                       <div>
                         <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Full Name</label>
                         <input 
                            type="text" 
                            required
                            value={signupName}
                            onChange={(e) => setSignupName(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500"
                            placeholder="John Doe"
                         />
                      </div>
                      <div>
                         <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Email Address</label>
                         <input 
                            type="email" 
                            required
                            value={signupEmail}
                            onChange={(e) => setSignupEmail(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500"
                            placeholder="name@example.com"
                         />
                      </div>
                      <div>
                         <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Password</label>
                         <input 
                            type="password" 
                            required
                            value={signupPassword}
                            onChange={(e) => setSignupPassword(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500"
                            placeholder="Create a password"
                         />
                      </div>

                      <button 
                        type="submit" 
                        disabled={loading}
                        className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2 mt-2"
                      >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>Sign Up <ArrowRight size={18} /></>
                        )}
                      </button>
                   </form>
               </div>
           )}

           {/* Reuse existing blocks for VERIFY_EMAIL, FORGOT_PASSWORD, EMAIL_SENT, RESET_PASSWORD as provided in prompt but ensure they use local handlers which are now safe */}
           
           {/* ... VERIFY_EMAIL block ... */}
           {view === 'VERIFY_EMAIL' && (
               <div className="animate-in slide-in-from-right duration-300 text-center">
                   <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6 text-emerald-600 dark:text-emerald-400">
                       <Mail size={32} />
                   </div>
                   <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Verify your email</h2>
                   <p className="text-slate-500 dark:text-slate-400 mb-8 text-sm">
                       We've sent a verification code to <span className="font-semibold text-slate-900 dark:text-white">{signupEmail}</span>.
                       Enter the code below to verify your account.
                   </p>

                   <form onSubmit={handleVerificationSubmit}>
                       <div className="flex justify-center gap-2 mb-8">
                           {verificationCode.map((digit, idx) => (
                               <input
                                   key={idx}
                                   id={`code-${idx}`}
                                   type="text"
                                   maxLength={1}
                                   value={digit}
                                   onChange={(e) => handleVerificationCodeChange(idx, e.target.value)}
                                   className="w-12 h-14 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 rounded-lg text-center text-xl font-bold text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                               />
                           ))}
                       </div>

                       <button 
                            type="submit"
                            disabled={loading}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Verify & Login"}
                       </button>
                   </form>
                   <button 
                        onClick={() => setView('SIGNUP')}
                        className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 mt-4"
                   >
                       Change email address
                   </button>
               </div>
           )}

           {/* ... FORGOT_PASSWORD ... */}
           {view === 'FORGOT_PASSWORD' && (
             <div className="animate-in slide-in-from-right duration-300">
                <button 
                    onClick={() => setView('LOGIN')}
                    className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 text-sm mb-6 transition-colors"
                >
                    <ArrowLeft size={16} /> Back to Login
                </button>
                <div className="text-center mb-8">
                    <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600 dark:text-emerald-400">
                        <Lock size={24} />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Forgot Password?</h2>
                    <p className="text-slate-500 dark:text-slate-400">Enter your email and we'll send you a link to reset your password.</p>
                </div>

                <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Email Address</label>
                        <input 
                            type="email" 
                            required
                            value={resetEmail}
                            onChange={(e) => setResetEmail(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400"
                            placeholder="name@example.com"
                        />
                    </div>
                    <button 
                        type="submit" 
                        disabled={loading}
                        className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                    >
                        {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Send Reset Link"}
                    </button>
                </form>
             </div>
           )}

           {/* ... EMAIL_SENT ... */}
           {view === 'EMAIL_SENT' && (
               <div className="animate-in zoom-in duration-300 text-center">
                   <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6 text-emerald-600 dark:text-emerald-400">
                       <Mail size={32} />
                   </div>
                   <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Check your email</h2>
                   <p className="text-slate-500 dark:text-slate-400 mb-8">
                       We've sent a password reset link to <span className="font-semibold text-slate-900 dark:text-white">{resetEmail}</span>
                   </p>
                   
                   <div className="space-y-3">
                        <button 
                            onClick={() => setView('RESET_PASSWORD')}
                            className="w-full bg-slate-900 dark:bg-slate-800 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-slate-800 dark:hover:bg-slate-700 transition-colors mb-4 border border-slate-700"
                        >
                            <ExternalLink size={16} /> Demo: Open Reset Link
                        </button>
                       <button 
                           onClick={() => setView('LOGIN')}
                           className="flex items-center justify-center gap-2 text-slate-500 hover:text-slate-800 dark:hover:text-white text-sm mx-auto mt-6 transition-colors"
                       >
                           <ArrowLeft size={16} /> Back to Login
                       </button>
                   </div>
               </div>
           )}

           {/* ... RESET_PASSWORD ... */}
           {view === 'RESET_PASSWORD' && (
               <div className="animate-in slide-in-from-right duration-300">
                   <div className="text-center mb-8">
                        <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600 dark:text-emerald-400">
                            <CheckCircle size={24} />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Set new password</h2>
                        <p className="text-slate-500 dark:text-slate-400">Must be at least 6 characters.</p>
                    </div>

                    <form onSubmit={handleResetPasswordSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">New Password</label>
                            <input 
                                type="password" 
                                required
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400"
                                placeholder="••••••••"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-500 dark:text-slate-400 mb-1.5">Confirm Password</label>
                            <input 
                                type="password" 
                                required
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors placeholder-slate-400"
                                placeholder="••••••••"
                            />
                        </div>
                        <button 
                            type="submit" 
                            disabled={loading}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Reset Password"}
                        </button>
                    </form>
                     <button 
                           onClick={() => setView('LOGIN')}
                           className="flex items-center justify-center gap-2 text-slate-500 hover:text-slate-800 dark:hover:text-white text-sm mx-auto mt-6 transition-colors"
                       >
                           <ArrowLeft size={16} /> Cancel
                       </button>
               </div>
           )}

        </div>
      </div>
    );
};