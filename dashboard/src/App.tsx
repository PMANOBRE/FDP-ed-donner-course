import { useEffect, useState } from "react";
import { ClaimPage } from "./ClaimPage";
import { InstructionsPage } from "./InstructionsPage";
import { QueuePage } from "./QueuePage";

function useHash() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => {
      setHash(window.location.hash);
    };
    window.addEventListener("hashchange", onChange);
    return () => {
      window.removeEventListener("hashchange", onChange);
    };
  }, []);
  return hash;
}

function Page({ hash }: Readonly<{ hash: string }>) {
  if (hash === "#/instructions") return <InstructionsPage />;
  const claim = /^#\/claims\/([^/]+)$/.exec(hash);
  if (claim) {
    const claimId = decodeURIComponent(claim[1]);
    return <ClaimPage key={claimId} claimId={claimId} />;
  }
  return <QueuePage />;
}

export function App() {
  const hash = useHash();
  const onInstructions = hash === "#/instructions";
  return (
    <>
      <header className="header">
        <a className="brand" href="#/">
          UnderCover <span className="tagline">Claims desk</span>
        </a>
        <nav aria-label="Main">
          <a href="#/" aria-current={onInstructions ? undefined : "page"}>
            Queue
          </a>
          <a
            href="#/instructions"
            aria-current={onInstructions ? "page" : undefined}
          >
            Instructions
          </a>
        </nav>
      </header>
      <main className="page">
        <Page hash={hash} />
      </main>
    </>
  );
}
