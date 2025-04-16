import streamlit as st
from mistralai import Mistral
import fitz
from pathlib import Path
import os

OUTPUT_DIR = Path("output")

model = "mistral-large-latest"

client = Mistral(api_key=os.environ['MISTRAL_API_KEY'])

def get_fec(invoice):
  chat_response = client.chat.complete(
      model=model,
      messages=[{"role":"user", "content":"Crée et retourne uniquement sans explication juste le csv des écritures comptables en format FEC (fichiers des écritures comptables) pour la saisie comptable de cette facture: \n"+invoice}]
  )

  return chat_response.choices[0].message.content


def process_files(uploaded_file):
    res = ""
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        file_path = OUTPUT_DIR / uploaded_file.name
        file_path.write_bytes(uploaded_file.getbuffer())
        
        extracted_text = ""
        # Open the PDF file
        pdf_document = fitz.open(file_path)
        
        for page in pdf_document:
            # Perform OCR using get_textpage_ocr
            textpage_ocr = page.get_textpage_ocr(flags=3, dpi=72, full=False, tessdata=None)

            # Extract text from the OCR result
            extracted_text +=  textpage_ocr.extractText()
        
        # Close the PDF document
        pdf_document.close()

        # Convert the OCR result to FEC using LLM
        res = get_fec(extracted_text)

    except Exception as e:
        st.error(f"Erreur avec {uploaded_file.name}: {str(e)}")
    return res

# Interface utilisateur
def main():
    st.title("📊 Reconnaissance Automatique des Factures")
    
    uploaded_file = st.file_uploader(
        "Télécharger votre Facture en format PDF",
        accept_multiple_files=False,
        type=["pdf"]
    ) 

    if st.button("Démarrer la conversion FEC"):
        if uploaded_file:
            status_placeholder = st.empty()
            status_placeholder.info(f"Traitement de {uploaded_file.name} ⌛")
            results = process_files(uploaded_file)
            if results != "":
                st.success("✅ Conversion terminée avec succès !")
                st.write(results)
                st.write("""### Explications des champs :
- **JournalCode** : Code du journal (ici, "AC" pour Journal d'achat).
- **JournalLib** : Libellé du journal (ici, "Journal d'achat").
- **EcritureNum** : Numéro de l'écriture.
- **EcritureDate** : Date de l'écriture (format AAAAMMJJ).
- **CompteNum** : Numéro du compte.
- **CompteLib** : Libellé du compte.
- **CompAuxNum** : Numéro du compte auxiliaire (optionnel).
- **CompAuxLib** : Libellé du compte auxiliaire (optionnel).
- **PieceRef** : Référence de la pièce justificative (ici, le numéro de la facture).
- **PieceDate** : Date de la pièce justificative (format AAAAMMJJ).
- **EcritureLib** : Libellé de l'écriture.
- **Debit** : Montant débité.
- **Credit** : Montant crédité.
- **EcritureLet** : Lettre de l'écriture (optionnel).
- **DateLet** : Date de la lettre de l'écriture (optionnel).
- **ValidDate** : Date de validation (optionnel).
- **Montantdevise** : Montant en devise (optionnel).
- **Idevise** : Code de la devise (optionnel).

### Remarques :

- Assurez-vous que les comptes utilisés correspondent bien à votre plan comptable.
- Si la TVA est applicable, il faudra ajouter une ligne supplémentaire pour enregistrer la TVA déductible.
- Le format FEC peut varier légèrement en fonction des logiciels comptables, mais les champs principaux restent généralement les mêmes.

Ces écritures comptables permettent de refléter correctement la facture dans votre comptabilité.""")

if __name__ == "__main__":
    main()
