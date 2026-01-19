
import React from 'react';
import { Calendar, CheckCircle } from 'lucide-react';
import { Tutor, User, Session } from '../../types';
import { Modal } from '../../components/shared/UI';

interface BookingModalProps {
    bookingStep: number;
    setBookingStep: (step: number) => void;
    selectedTutor: Tutor | null;
    selectedSlot: string | null;
    onSlotSelect: (e: React.MouseEvent, tutor: Tutor, slot: string) => void;
    onConfirm: () => void;
    onReturnToDashboard: () => void;
}

export const BookingModal: React.FC<BookingModalProps> = ({ 
    bookingStep, setBookingStep, selectedTutor, selectedSlot, onSlotSelect, onConfirm, onReturnToDashboard
}) => {
    return (
      <Modal isOpen={bookingStep > 0} onClose={() => setBookingStep(0)} title="Book Session">
          {bookingStep === 1 && selectedTutor && (
              <div className="space-y-4">
                  <p className="text-slate-600 dark:text-slate-400">Select a time for your session with <span className="font-semibold text-slate-900 dark:text-white">{selectedTutor.name}</span>.</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {selectedTutor.availability.map(slot => (
                          <button 
                            key={slot} 
                            onClick={(e) => onSlotSelect(e, selectedTutor, slot)}
                            className="p-3 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 dark:hover:border-emerald-500/50 transition-all text-sm text-center"
                          >
                              <div className="font-semibold text-emerald-600 dark:text-emerald-400">{new Date(slot).toLocaleDateString(undefined, {weekday: 'short'})}</div>
                              <div className="text-slate-600 dark:text-slate-300">{new Date(slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                          </button>
                      ))}
                  </div>
              </div>
          )}
          {bookingStep === 2 && selectedTutor && selectedSlot && (
              <div className="space-y-6">
                  <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 flex gap-4">
                      <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                          <Calendar size={24} />
                      </div>
                      <div>
                          <h4 className="font-semibold text-slate-900 dark:text-white">Session Details</h4>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{selectedTutor.subject} • 1 Hour</p>
                          <p className="text-sm text-emerald-600 dark:text-emerald-400 mt-1 font-medium">{new Date(selectedSlot).toLocaleString()}</p>
                      </div>
                  </div>
                  
                  <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Hourly Rate</span>
                          <span className="font-medium">${selectedTutor.hourlyRate.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Service Fee</span>
                          <span className="font-medium">$5.00</span>
                      </div>
                      <div className="border-t border-slate-200 dark:border-slate-800 pt-3 flex justify-between font-bold text-lg">
                          <span>Total</span>
                          <span>${(selectedTutor.hourlyRate + 5).toFixed(2)}</span>
                      </div>
                  </div>

                  <button onClick={onConfirm} className="w-full bg-emerald-600 text-white py-3 rounded-xl font-bold hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-500/20">
                      Confirm & Pay
                  </button>
              </div>
          )}
          {bookingStep === 3 && (
              <div className="text-center py-6">
                  <div className="w-20 h-20 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-6 animate-in zoom-in duration-300">
                      <CheckCircle size={40} />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Booking Confirmed!</h3>
                  <p className="text-slate-500 dark:text-slate-400 mb-8">You're all set. A calendar invite has been sent to your email.</p>
                  <button onClick={onReturnToDashboard} className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-8 py-3 rounded-xl font-semibold hover:opacity-90 transition-opacity">
                      Back to Dashboard
                  </button>
              </div>
          )}
      </Modal>
    );
};
