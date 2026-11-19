import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getInstructions } from "./api";
import { Pending } from "./Pending";
import { useData } from "./useData";

export function InstructionsPage() {
  const instructions = useData("instructions", getInstructions);
  if (instructions.state !== "ready") {
    return <Pending loaded={instructions} missing="Instructions not found" />;
  }
  return (
    <>
      <h1>The agent&apos;s instructions</h1>
      <p className="muted">
        Read only. The agent starts every claim with these instructions,
        followed by the policy wording.
      </p>
      <article className="panel prose">
        <Markdown remarkPlugins={[remarkGfm]}>
          {instructions.data.text}
        </Markdown>
      </article>
    </>
  );
}
