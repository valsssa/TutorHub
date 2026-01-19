const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
  defaults: {
    headers: {
      common: {},
    },
  },
  interceptors: {
    request: {
      use: jest.fn(),
      eject: jest.fn(),
    },
    response: {
      use: jest.fn(),
      eject: jest.fn(),
    },
  },
};

const axiosMock: any = jest.fn(() => mockAxiosInstance);

axiosMock.create = jest.fn(() => mockAxiosInstance);
axiosMock.isAxiosError = jest.fn(() => false);
axiosMock.CancelToken = {
  source: jest.fn(() => ({
    token: "token",
    cancel: jest.fn(),
  })),
};

axiosMock.get = mockAxiosInstance.get;
axiosMock.post = mockAxiosInstance.post;
axiosMock.put = mockAxiosInstance.put;
axiosMock.patch = mockAxiosInstance.patch;
axiosMock.delete = mockAxiosInstance.delete;
axiosMock.defaults = mockAxiosInstance.defaults;
axiosMock.interceptors = mockAxiosInstance.interceptors;

export default axiosMock;
