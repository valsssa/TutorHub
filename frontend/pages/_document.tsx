import Document, {
  DocumentContext,
  DocumentInitialProps,
  Head,
  Html,
  Main,
  NextScript,
} from 'next/document';

interface MyDocumentProps extends DocumentInitialProps {
  nonce?: string;
}

class MyDocument extends Document<MyDocumentProps> {
  static async getInitialProps(ctx: DocumentContext): Promise<MyDocumentProps> {
    const initialProps = await Document.getInitialProps(ctx);
    const nonce = (ctx.req?.headers['x-nonce'] as string | undefined) ?? undefined;

    return {
      ...initialProps,
      nonce,
    };
  }

  render() {
    const nonce = this.props.nonce;

    return (
      <Html lang="en">
        <Head>
          {nonce ? <meta httpEquiv="Content-Security-Policy-Nonce" content={nonce} /> : null}
        </Head>
        <body>
          <Main />
          <NextScript nonce={nonce} />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
