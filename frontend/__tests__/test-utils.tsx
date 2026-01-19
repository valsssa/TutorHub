import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ToastProvider } from '@/components/ToastContainer';

interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  return <ToastProvider>{children}</ToastProvider>;
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
